from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from typing import List
from models import Farmaceutica
from database import get_session

router = APIRouter(prefix="/farmaceuticas", tags=["Farmacêuticas"])


@router.post("/", response_model=Farmaceutica)
def create_farmaceutica(farmaceutica: Farmaceutica, session: Session = Depends(get_session), current_user = Depends(get_current_user)):
    if current_user.tipo != "farmaceutica" and current_user.tipo != "admin":
        raise HTTPException(status_code=403, detail="Acesso restrito a farmacêuticas")

    nova_farmaceutica = Farmaceutica(
        nome=farmaceutica.nome,
        cnpj=farmaceutica.cnpj,
        contato=farmaceutica.contato,
        id_usuario=current_user.id
    )
    session.add(nova_farmaceutica)

    current_user.ativo = True
    session.add(current_user)
    session.commit()

    return nova_farmaceutica


@router.get("/", response_model=List[Farmaceutica])
def list_farmaceuticas(session: Session = Depends(get_session)):
    farmaceuticas = session.exec(select(Farmaceutica)).all()
    return farmaceuticas


@router.get("/{farmaceutica_id}", response_model=Farmaceutica)
def get_farmaceutica(farmaceutica_id: int, session: Session = Depends(get_session)):
    farmaceutica = session.get(Farmaceutica, farmaceutica_id)
    if not farmaceutica:
        raise HTTPException(status_code=404, detail="Farmacêutica não encontrada")
    return farmaceutica


@router.put("/{farmaceutica_id}", response_model=Farmaceutica)
def update_farmaceutica(
    farmaceutica_id: int, 
    farmaceutica: Farmaceutica, 
    session: Session = Depends(get_session)
):
    db_farmaceutica = session.get(Farmaceutica, farmaceutica_id)
    if not db_farmaceutica:
        raise HTTPException(status_code=404, detail="Farmacêutica não encontrada")
    
    farmaceutica_data = farmaceutica.model_dump(exclude_unset=True, exclude={"id_farmaceutica"})
    for key, value in farmaceutica_data.items():
        setattr(db_farmaceutica, key, value)
    
    session.add(db_farmaceutica)
    session.commit()
    session.refresh(db_farmaceutica)
    return db_farmaceutica


@router.delete("/{farmaceutica_id}")
def delete_farmaceutica(farmaceutica_id: int, session: Session = Depends(get_session)):
    farmaceutica = session.get(Farmaceutica, farmaceutica_id)
    if not farmaceutica:
        raise HTTPException(status_code=404, detail="Farmacêutica não encontrada")
    
    session.delete(farmaceutica)
    session.commit()
    return {"message": "Farmacêutica deletada com sucesso"}