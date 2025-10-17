from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from typing import List
from datetime import datetime
from models import Lote
from database import get_session

router = APIRouter(prefix="/lotes", tags=["Lotes"])


@router.post("/", response_model=Lote)
def create_lote(lote: Lote, session: Session = Depends(get_session)):
    session.add(lote)
    session.commit()
    session.refresh(lote)
    return lote


@router.get("/", response_model=List[Lote])
def list_lotes(session: Session = Depends(get_session)):
    lotes = session.exec(select(Lote)).all()
    return lotes


@router.get("/{lote_id}", response_model=Lote)
def get_lote(lote_id: int, session: Session = Depends(get_session)):
    lote = session.get(Lote, lote_id)
    if not lote:
        raise HTTPException(status_code=404, detail="Lote não encontrado")
    return lote


@router.get("/medicamento/{medicamento_id}", response_model=List[Lote])
def list_lotes_by_medicamento(
    medicamento_id: int, 
    session: Session = Depends(get_session)
):
    lotes = session.exec(
        select(Lote).where(Lote.id_medicamento == medicamento_id)
    ).all()
    return lotes


@router.get("/vencidos/", response_model=List[Lote])
def list_lotes_vencidos(session: Session = Depends(get_session)):
    lotes = session.exec(
        select(Lote).where(Lote.data_vencimento < datetime.now())
    ).all()
    return lotes


@router.put("/{lote_id}", response_model=Lote)
def update_lote(
    lote_id: int, 
    lote: Lote, 
    session: Session = Depends(get_session)
):
    db_lote = session.get(Lote, lote_id)
    if not db_lote:
        raise HTTPException(status_code=404, detail="Lote não encontrado")
    
    lote_data = lote.model_dump(exclude_unset=True, exclude={"id_lote"})
    for key, value in lote_data.items():
        setattr(db_lote, key, value)
    
    session.add(db_lote)
    session.commit()
    session.refresh(db_lote)
    return db_lote


@router.delete("/{lote_id}")
def delete_lote(lote_id: int, session: Session = Depends(get_session)):
    lote = session.get(Lote, lote_id)
    if not lote:
        raise HTTPException(status_code=404, detail="Lote não encontrado")
    
    session.delete(lote)
    session.commit()
    return {"message": "Lote deletado com sucesso"}