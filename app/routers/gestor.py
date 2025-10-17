from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from typing import List
from models import Gestor
from database import get_session

router = APIRouter(prefix="/gestores", tags=["Gestores"])


@router.post("/", response_model=Gestor)
def create_gestor(gestor: Gestor, session: Session = Depends(get_session)):
    session.add(gestor)
    session.commit()
    session.refresh(gestor)
    return gestor


@router.get("/", response_model=List[Gestor])
def list_gestores(session: Session = Depends(get_session)):
    gestores = session.exec(select(Gestor)).all()
    return gestores


@router.get("/{gestor_id}", response_model=Gestor)
def get_gestor(gestor_id: int, session: Session = Depends(get_session)):
    gestor = session.get(Gestor, gestor_id)
    if not gestor:
        raise HTTPException(status_code=404, detail="Gestor não encontrado")
    return gestor


@router.put("/{gestor_id}", response_model=Gestor)
def update_gestor(
    gestor_id: int, 
    gestor: Gestor, 
    session: Session = Depends(get_session)
):
    db_gestor = session.get(Gestor, gestor_id)
    if not db_gestor:
        raise HTTPException(status_code=404, detail="Gestor não encontrado")
    
    gestor_data = gestor.model_dump(exclude_unset=True, exclude={"id_gestor"})
    for key, value in gestor_data.items():
        setattr(db_gestor, key, value)
    
    session.add(db_gestor)
    session.commit()
    session.refresh(db_gestor)
    return db_gestor


@router.delete("/{gestor_id}")
def delete_gestor(gestor_id: int, session: Session = Depends(get_session)):
    gestor = session.get(Gestor, gestor_id)
    if not gestor:
        raise HTTPException(status_code=404, detail="Gestor não encontrado")
    
    session.delete(gestor)
    session.commit()
    return {"message": "Gestor deletado com sucesso"}