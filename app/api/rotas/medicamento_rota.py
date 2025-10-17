from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.database import get_session
from app.models.medicamento import Medicamento
from app.models.farmaceutica import Farmaceutica

router = APIRouter(prefix="/medicamentos", tags=["Medicamentos"])

@router.post("/", response_model=Medicamento)
def criar_medicamento(med: Medicamento, session: Session = Depends(get_session)):
    # validar FK
    if not session.get(Farmaceutica, med.id_farmaceutica):
        raise HTTPException(status_code=404, detail="Farmacêutica não encontrada")
    session.add(med)
    session.commit()
    session.refresh(med)
    return med

@router.get("/", response_model=list[Medicamento])
def listar_medicamentos(session: Session = Depends(get_session)):
    return session.exec(select(Medicamento)).all()

@router.get("/{med_id}", response_model=Medicamento)
def buscar_medicamento(med_id: int, session: Session = Depends(get_session)):
    med = session.get(Medicamento, med_id)
    if not med:
        raise HTTPException(status_code=404, detail="Medicamento não encontrado")
    return med

@router.put("/{med_id}", response_model=Medicamento)
def atualizar_medicamento(med_id: int, dados: Medicamento, session: Session = Depends(get_session)):
    med = session.get(Medicamento, med_id)
    if not med:
        raise HTTPException(status_code=404, detail="Medicamento não encontrado")
    med.nome = dados.nome
    med.id_farmaceutica = dados.id_farmaceutica
    session.commit()
    session.refresh(med)
    return med

@router.delete("/{med_id}")
def deletar_medicamento(med_id: int, session: Session = Depends(get_session)):
    med = session.get(Medicamento, med_id)
    if not med:
        raise HTTPException(status_code=404, detail="Medicamento não encontrado")
    session.delete(med)
    session.commit()
    return {"ok": True, "mensagem": "Medicamento removido"}
