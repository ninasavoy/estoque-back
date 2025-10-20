from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from typing import List
from models import UBS
from database import get_session

router = APIRouter(prefix="/ubs", tags=["UBS"])


@router.post("/", response_model=UBS)
def create_ubs(ubs: UBS, session: Session = Depends(get_session)):
    session.add(ubs)
    session.commit()
    session.refresh(ubs)
    return ubs


@router.get("/", response_model=List[UBS])
def list_ubs(session: Session = Depends(get_session)):
    ubs_list = session.exec(select(UBS)).all()
    return ubs_list


@router.get("/{ubs_id}", response_model=UBS)
def get_ubs(ubs_id: int, session: Session = Depends(get_session)):
    ubs = session.get(UBS, ubs_id)
    if not ubs:
        raise HTTPException(status_code=404, detail="UBS não encontrada")
    return ubs


@router.get("/sus/{sus_id}", response_model=List[UBS])
def list_ubs_by_sus(
    sus_id: int, 
    session: Session = Depends(get_session)
):
    ubs_list = session.exec(
        select(UBS).where(UBS.id_sus == sus_id)
    ).all()
    return ubs_list


@router.put("/{ubs_id}", response_model=UBS)
def update_ubs(
    ubs_id: int, 
    ubs: UBS, 
    session: Session = Depends(get_session)
):
    db_ubs = session.get(UBS, ubs_id)
    if not db_ubs:
        raise HTTPException(status_code=404, detail="UBS não encontrada")
    
    ubs_data = ubs.model_dump(exclude_unset=True, exclude={"id_ubs"})
    for key, value in ubs_data.items():
        setattr(db_ubs, key, value)
    
    session.add(db_ubs)
    session.commit()
    session.refresh(db_ubs)
    return db_ubs


@router.delete("/{ubs_id}")
def delete_ubs(ubs_id: int, session: Session = Depends(get_session)):
    ubs = session.get(UBS, ubs_id)
    if not ubs:
        raise HTTPException(status_code=404, detail="UBS não encontrada")
    
    session.delete(ubs)
    session.commit()
    return {"message": "UBS deletada com sucesso"}