from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from typing import List
from auth.dependencies import get_current_user
from models import User, UserBase
from database import get_session

router = APIRouter(prefix="/users", tags=["Users"])

# meio que a register já faz isso
# @router.post("/", response_model=User)
# def create_user(user: UserBase, session: Session = Depends(get_session)):
#     db_user = User.model_validate(user)
#     session.add(db_user)
#     session.commit()
#     session.refresh(db_user)
#     return db_user


@router.get("/", response_model=List[User])
def list_users(session: Session = Depends(get_session), current_user = Depends(get_current_user)):
    if current_user.tipo != "admin":
        raise HTTPException(status_code=403, detail="Acesso restrito a administradores")
    
    users = session.exec(select(User)).all()
    return users


@router.get("/{user_id}", response_model=User)
def get_user(user_id: int, session: Session = Depends(get_session), current_user = Depends(get_current_user)):
    if current_user.tipo != "admin":
        raise HTTPException(status_code=403, detail="Acesso restrito a administradores")
    
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return user


@router.put("/{user_id}", response_model=User)
def update_user(user_id: int, user: UserBase, session: Session = Depends(get_session), current_user = Depends(get_current_user)):
    if current_user.tipo != "admin":
        raise HTTPException(status_code=403, detail="Acesso restrito a administradores")
    
    db_user = session.get(User, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    user_data = user.model_dump(exclude_unset=True)
    for key, value in user_data.items():
        setattr(db_user, key, value)
    
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


@router.delete("/{user_id}")
def delete_user(user_id: int, session: Session = Depends(get_session), current_user = Depends(get_current_user)):
    if current_user.tipo != "admin":
        raise HTTPException(status_code=403, detail="Acesso restrito a administradores")
    
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    session.delete(user)
    session.commit()
    return {"message": "Usuário deletado com sucesso"}