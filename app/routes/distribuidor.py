from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from typing import List
from models import Distribuidor
from database import get_session

router = APIRouter(prefix="/distribuidores", tags=["Distribuidores"])


@router.post("/", response_model=Distribuidor)
def create_distribuidor(distribuidor: Distribuidor, session: Session = Depends(get_session)):
    session.add(distribuidor)
    session.commit()
    session.refresh(distribuidor)
    return distribuidor


@router.get("/", response_model=List[Distribuidor])
def list_distribuidores(session: Session = Depends(get_session)):
    distribuidores = session.exec(select(Distribuidor)).all()
    return distribuidores


@router.get("/{distribuidor_id}", response_model=Distribuidor)
def get_distribuidor(distribuidor_id: int, session: Session = Depends(get_session)):
    distribuidor = session.get(Distribuidor, distribuidor_id)
    if not distribuidor:
        raise HTTPException(status_code=404, detail="Distribuidor não encontrado")
    return distribuidor


@router.put("/{distribuidor_id}", response_model=Distribuidor)
def update_distribuidor(
    distribuidor_id: int, 
    distribuidor: Distribuidor, 
    session: Session = Depends(get_session)
):
    db_distribuidor = session.get(Distribuidor, distribuidor_id)
    if not db_distribuidor:
        raise HTTPException(status_code=404, detail="Distribuidor não encontrado")
    
    distribuidor_data = distribuidor.model_dump(exclude_unset=True, exclude={"id_distribuidor"})
    for key, value in distribuidor_data.items():
        setattr(db_distribuidor, key, value)
    
    session.add(db_distribuidor)
    session.commit()
    session.refresh(db_distribuidor)
    return db_distribuidor


@router.delete("/{distribuidor_id}")
def delete_distribuidor(distribuidor_id: int, session: Session = Depends(get_session)):
    distribuidor = session.get(Distribuidor, distribuidor_id)
    if not distribuidor:
        raise HTTPException(status_code=404, detail="Distribuidor não encontrado")
    
    session.delete(distribuidor)
    session.commit()
    return {"message": "Distribuidor deletado com sucesso"}