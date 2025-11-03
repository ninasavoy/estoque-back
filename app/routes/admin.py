from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from typing import List
from models import Administrador
from database import get_session

router = APIRouter(prefix="/admin", tags=["Admins"])

@router.post("/", response_model=Administrador)
def create_admin(admin: Administrador, session: Session = Depends(get_session)):
    session.add(admin)
    session.commit()
    session.refresh(admin)
    return admin

@router.get("/", response_model=List[Administrador])
def list_admins(session: Session = Depends(get_session)):
    admins = session.exec(select(Administrador)).all()
    return admins

@router.get("/{admin_id}", response_model=Administrador)
def get_admin(admin_id: int, session: Session = Depends(get_session)):
    admin = session.get(Administrador, admin_id)
    if not admin:
        raise HTTPException(status_code=404, detail="Administrador não encontrado")
    return admin

@router.put("/{admin_id}", response_model=Administrador)
def update_admin(
    admin_id: int, 
    admin: Administrador, 
    session: Session = Depends(get_session)
):
    db_admin = session.get(Administrador, admin_id)
    if not db_admin:
        raise HTTPException(status_code=404, detail="Administrador não encontrado")
    
    admin_data = admin.model_dump(exclude_unset=True, exclude={"id_admin"})
    for key, value in admin_data.items():
        setattr(db_admin, key, value)
    
    session.add(db_admin)
    session.commit()
    session.refresh(db_admin)
    return db_admin

@router.delete("/{admin_id}")
def delete_admin(admin_id: int, session: Session = Depends(get_session)):
    admin = session.get(Administrador, admin_id)
    if not admin:
        raise HTTPException(status_code=404, detail="Administrador não encontrado")
    
    session.delete(admin)
    session.commit()
    return {"message": "Administrador deletado com sucesso"}
