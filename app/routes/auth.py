from fastapi import APIRouter, HTTPException, Depends, status
from sqlmodel import Session, select
from pydantic import BaseModel
from models import User, UserBase
from database import get_session
from auth.dependencies import create_access_token, get_current_user
from auth.permissions import get_user_permissions
import hashlib

router = APIRouter(prefix="/auth", tags=["Autenticação"])


class LoginRequest(BaseModel):
    email: str
    senha: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict
    permissions: list


class RegisterRequest(BaseModel):
    nome: str
    email: str
    senha: str
    tipo: str



def hash_password(password: str) -> str:
    """Hash da senha usando SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se a senha corresponde ao hash"""
    return hash_password(plain_password) == hashed_password


@router.post("/register", response_model=User)
def register(
    user_data: RegisterRequest,
    session: Session = Depends(get_session)
):
    """Registra um novo usuário"""
    # Verifica se o email já existe
    existing_user = session.exec(
        select(User).where(User.email == user_data.email)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já cadastrado"
        )
    
    # Valida o tipo de usuário
    valid_types = ["farmaceutica", "distribuidor", "sus", "ubs", "paciente"]
    if user_data.tipo not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de usuário inválido. Use: {', '.join(valid_types)}"
        )
    
    # Cria o usuário com senha hasheada
    user = User(
        nome=user_data.nome,
        email=user_data.email,
        senha_hash=hash_password(user_data.senha),  # Assumindo que vem como senha plain
        tipo=user_data.tipo
    )
    
    session.add(user)
    session.commit()
    session.refresh(user)
    
    return user


@router.post("/login", response_model=LoginResponse)
def login(
    login_data: LoginRequest,
    session: Session = Depends(get_session)
):
    """Faz login e retorna o token JWT"""
    # Busca o usuário pelo email
    user = session.exec(
        select(User).where(User.email == login_data.email)
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos"
        )
    
    # Verifica a senha
    if not verify_password(login_data.senha, user.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos"
        )
    
    # Cria o token
    access_token = create_access_token(data={"sub": user.id})
    
    # Obtém as permissões do usuário
    permissions = get_user_permissions(user.tipo)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "nome": user.nome,
            "email": user.email,
            "tipo": user.tipo
        },
        "permissions": permissions
    }


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    """Retorna informações do usuário atual"""
    permissions = get_user_permissions(current_user.tipo)
    
    return {
        "id": current_user.id,
        "nome": current_user.nome,
        "email": current_user.email,
        "tipo": current_user.tipo,
        "permissions": permissions
    }


@router.post("/change-password")
def change_password(
    old_password: str,
    new_password: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Altera a senha do usuário"""
    # Verifica a senha antiga
    if not verify_password(old_password, current_user.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Senha atual incorreta"
        )
    
    # Atualiza a senha
    current_user.senha_hash = hash_password(new_password)
    session.add(current_user)
    session.commit()
    
    return {"message": "Senha alterada com sucesso"}