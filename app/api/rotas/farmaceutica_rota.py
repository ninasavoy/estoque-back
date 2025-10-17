from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.database import get_session
from app.models.farmaceutica import Farmaceutica

router = APIRouter(prefix="/farmaceuticas", tags=["Farmacêuticas"])

@router.post("/", response_model=Farmaceutica)
def criar_farmaceutica(farm: Farmaceutica, session: Session = Depends(get_session)):
    session.add(farm)
    session.commit()
    session.refresh(farm)
    return farm

@router.get("/", response_model=list[Farmaceutica])
def listar_farmaceuticas(session: Session = Depends(get_session)):
    return session.exec(select(Farmaceutica)).all()

@router.get("/{farm_id}", response_model=Farmaceutica)
def buscar_farmaceutica(farm_id: int, session: Session = Depends(get_session)):
    farm = session.get(Farmaceutica, farm_id)
    if not farm:
        raise HTTPException(status_code=404, detail="Farmacêutica não encontrada")
    return farm

@router.put("/{farm_id}", response_model=Farmaceutica)
def atualizar_farmaceutica(farm_id: int, dados: Farmaceutica, session: Session = Depends(get_session)):
    farm = session.get(Farmaceutica, farm_id)
    if not farm:
        raise HTTPException(status_code=404, detail="Farmacêutica não encontrada")
    farm.nome = dados.nome
    farm.cnpj = dados.cnpj
    farm.contato = dados.contato
    session.commit()
    session.refresh(farm)
    return farm

@router.delete("/{farm_id}")
def deletar_farmaceutica(farm_id: int, session: Session = Depends(get_session)):
    farm = session.get(Farmaceutica, farm_id)
    if not farm:
        raise HTTPException(status_code=404, detail="Farmacêutica não encontrada")
    session.delete(farm)
    session.commit()
    return {"ok": True, "mensagem": "Farmacêutica deletada com sucesso"}
