from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.database import get_session
from app.models.lote import Lote
from app.models.medicamento import Medicamento

router = APIRouter(prefix="/lotes", tags=["Lotes"])

@router.post("/", response_model=Lote)
def criar_lote(lote: Lote, session: Session = Depends(get_session)):
    if not session.get(Medicamento, lote.id_medicamento):
        raise HTTPException(status_code=404, detail="Medicamento não encontrado")
    session.add(lote)
    session.commit()
    session.refresh(lote)
    return lote

@router.get("/", response_model=list[Lote])
def listar_lotes(session: Session = Depends(get_session)):
    return session.exec(select(Lote)).all()

@router.get("/{lote_id}", response_model=Lote)
def buscar_lote(lote_id: int, session: Session = Depends(get_session)):
    lote = session.get(Lote, lote_id)
    if not lote:
        raise HTTPException(status_code=404, detail="Lote não encontrado")
    return lote

@router.put("/{lote_id}", response_model=Lote)
def atualizar_lote(lote_id: int, dados: Lote, session: Session = Depends(get_session)):
    lote = session.get(Lote, lote_id)
    if not lote:
        raise HTTPException(status_code=404, detail="Lote não encontrado")
    lote.codigo_lote = dados.codigo_lote
    lote.data_fabricacao = dados.data_fabricacao
    lote.data_validade = dados.data_validade
    lote.quantidade_inicial = dados.quantidade_inicial
    session.commit()
    session.refresh(lote)
    return lote

@router.delete("/{lote_id}")
def deletar_lote(lote_id: int, session: Session = Depends(get_session)):
    lote = session.get(Lote, lote_id)
    if not lote:
        raise HTTPException(status_code=404, detail="Lote não encontrado")
    session.delete(lote)
    session.commit()
    return {"ok": True, "mensagem": "Lote removido com sucesso"}
