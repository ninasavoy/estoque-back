from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from typing import List
from models import Paciente
from database import get_session

router = APIRouter(prefix="/pacientes", tags=["Pacientes"])


@router.post("/", response_model=Paciente)
def create_paciente(paciente: Paciente, session: Session = Depends(get_session)):
    session.add(paciente)
    session.commit()
    session.refresh(paciente)
    return paciente


@router.get("/", response_model=List[Paciente])
def list_pacientes(session: Session = Depends(get_session)):
    pacientes = session.exec(select(Paciente)).all()
    return pacientes


@router.get("/{paciente_id}", response_model=Paciente)
def get_paciente(paciente_id: int, session: Session = Depends(get_session)):
    paciente = session.get(Paciente, paciente_id)
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente não encontrado")
    return paciente


@router.get("/ubs/{ubs_id}", response_model=List[Paciente])
def list_pacientes_by_ubs(
    ubs_id: int, 
    session: Session = Depends(get_session)
):
    pacientes = session.exec(
        select(Paciente).where(Paciente.id_ubs == ubs_id)
    ).all()
    return pacientes


@router.put("/{paciente_id}", response_model=Paciente)
def update_paciente(
    paciente_id: int, 
    paciente: Paciente, 
    session: Session = Depends(get_session)
):
    db_paciente = session.get(Paciente, paciente_id)
    if not db_paciente:
        raise HTTPException(status_code=404, detail="Paciente não encontrado")
    
    paciente_data = paciente.model_dump(exclude_unset=True, exclude={"id_paciente"})
    for key, value in paciente_data.items():
        setattr(db_paciente, key, value)
    
    session.add(db_paciente)
    session.commit()
    session.refresh(db_paciente)
    return db_paciente


@router.delete("/{paciente_id}")
def delete_paciente(paciente_id: int, session: Session = Depends(get_session)):
    paciente = session.get(Paciente, paciente_id)
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente não encontrado")
    
    session.delete(paciente)
    session.commit()
    return {"message": "Paciente deletado com sucesso"}