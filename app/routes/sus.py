from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from typing import List
from models import SUS
from database import get_session

router = APIRouter(prefix="/sus", tags=["SUS"])


@router.post("/", response_model=SUS)
def create_sus(sus: SUS, session: Session = Depends(get_session)):
    session.add(sus)
    session.commit()
    session.refresh(sus)
    return sus


@router.get("/", response_model=List[SUS])
def list_sus(session: Session = Depends(get_session)):
    sus_list = session.exec(select(SUS)).all()
    return sus_list


@router.get("/{sus_id}", response_model=SUS)
def get_sus(sus_id: int, session: Session = Depends(get_session)):
    sus = session.get(SUS, sus_id)
    if not sus:
        raise HTTPException(status_code=404, detail="SUS não encontrado")
    return sus


@router.get("/gestor/{gestor_id}", response_model=List[SUS])
def list_sus_by_gestor(
    gestor_id: int, 
    session: Session = Depends(get_session)
):
    sus_list = session.exec(
        select(SUS).where(SUS.id_gestor == gestor_id)
    ).all()
    return sus_list


@router.put("/{sus_id}", response_model=SUS)
def update_sus(
    sus_id: int, 
    sus: SUS, 
    session: Session = Depends(get_session)
):
    db_sus = session.get(SUS, sus_id)
    if not db_sus:
        raise HTTPException(status_code=404, detail="SUS não encontrado")
    
    sus_data = sus.model_dump(exclude_unset=True, exclude={"id_sus"})
    for key, value in sus_data.items():
        setattr(db_sus, key, value)
    
    session.add(db_sus)
    session.commit()
    session.refresh(db_sus)
    return db_sus


@router.delete("/{sus_id}")
def delete_sus(sus_id: int, session: Session = Depends(get_session)):
    sus = session.get(SUS, sus_id)
    if not sus:
        raise HTTPException(status_code=404, detail="SUS não encontrado")
    
    session.delete(sus)
    session.commit()
    return {"message": "SUS deletado com sucesso"}