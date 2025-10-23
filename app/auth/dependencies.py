from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session, select
from typing import Optional
from models import User
from database import get_session
import jwt
from datetime import datetime, timedelta

# Configurações JWT
SECRET_KEY = "chave-secreta"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 horas

security = HTTPBearer()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Cria um token JWT"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str):
    """Decodifica um token JWT"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado"
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_session)
) -> User:
    """Dependency para obter o usuário atual a partir do token"""
    token = credentials.credentials
    payload = decode_access_token(token)
    
    user_id: int = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas"
        )
    
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado"
        )
    
    return user


async def get_current_farmaceutica(
    current_user: User = Depends(get_current_user)
) -> User:
    """Verifica se o usuário é do tipo Farmacêutica"""
    if current_user.tipo != "farmaceutica":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso exclusivo para Farmacêuticas"
        )
    return current_user


async def get_current_distribuidor(
    current_user: User = Depends(get_current_user)
) -> User:
    """Verifica se o usuário é do tipo Distribuidor"""
    if current_user.tipo != "distribuidor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso exclusivo para Distribuidores"
        )
    return current_user


async def get_current_sus(
    current_user: User = Depends(get_current_user)
) -> User:
    """Verifica se o usuário é do tipo SUS"""
    if current_user.tipo != "sus":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso exclusivo para SUS"
        )
    return current_user


async def get_current_ubs(
    current_user: User = Depends(get_current_user)
) -> User:
    """Verifica se o usuário é do tipo UBS"""
    if current_user.tipo != "ubs":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso exclusivo para UBS"
        )
    return current_user


async def get_current_paciente(
    current_user: User = Depends(get_current_user)
) -> User:
    """Verifica se o usuário é do tipo Paciente"""
    if current_user.tipo != "paciente":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso exclusivo para Pacientes"
        )
    return current_user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    session: Session = Depends(get_session)
) -> Optional[User]:
    """Dependency para obter o usuário atual (opcional - não obriga autenticação)"""
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials, session)
    except HTTPException:
        return None