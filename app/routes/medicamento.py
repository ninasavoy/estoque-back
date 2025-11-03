from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from typing import List
from auth.dependencies import require_permissions
from auth.permissions import Permission
from models import Medicamento
from database import get_session

router = APIRouter(prefix="/medicamentos", tags=["Medicamentos"])


@router.post("/", response_model=Medicamento, dependencies=[require_permissions([Permission.CREATE_MEDICAMENTO])])
def create_medicamento(medicamento: Medicamento, session: Session = Depends(get_session)):
    session.add(medicamento)
    session.commit()
    session.refresh(medicamento)
    return medicamento


@router.get("/", response_model=List[Medicamento], dependencies=[require_permissions([Permission.LIST_MEDICAMENTO])])
def list_medicamentos(session: Session = Depends(get_session)):
    medicamentos = session.exec(select(Medicamento)).all()
    return medicamentos


@router.get("/{medicamento_id}", response_model=Medicamento, dependencies=[require_permissions([Permission.READ_MEDICAMENTO])])
def get_medicamento(medicamento_id: int, session: Session = Depends(get_session)):
    medicamento = session.get(Medicamento, medicamento_id)
    if not medicamento:
        raise HTTPException(status_code=404, detail="Medicamento não encontrado")
    return medicamento


@router.get("/farmaceutica/{farmaceutica_id}", response_model=List[Medicamento], dependencies=[require_permissions([Permission.LIST_MEDICAMENTO])])
def list_medicamentos_by_farmaceutica(
    farmaceutica_id: int, 
    session: Session = Depends(get_session)
):
    medicamentos = session.exec(
        select(Medicamento).where(Medicamento.id_farmaceutica == farmaceutica_id)
    ).all()
    return medicamentos


@router.put("/{medicamento_id}", response_model=Medicamento)
def update_medicamento(
    medicamento_id: int, 
    medicamento: Medicamento, 
    session: Session = Depends(get_session)
):
    db_medicamento = session.get(Medicamento, medicamento_id)
    if not db_medicamento:
        raise HTTPException(status_code=404, detail="Medicamento não encontrado")
    
    medicamento_data = medicamento.model_dump(exclude_unset=True, exclude={"id_medicamento"})
    for key, value in medicamento_data.items():
        setattr(db_medicamento, key, value)
    
    session.add(db_medicamento)
    session.commit()
    session.refresh(db_medicamento)
    return db_medicamento


@router.delete("/{medicamento_id}")
def delete_medicamento(medicamento_id: int, session: Session = Depends(get_session)):
    medicamento = session.get(Medicamento, medicamento_id)
    if not medicamento:
        raise HTTPException(status_code=404, detail="Medicamento não encontrado")
    
    session.delete(medicamento)
    session.commit()
    return {"message": "Medicamento deletado com sucesso"}