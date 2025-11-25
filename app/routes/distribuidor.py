from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from typing import List
from models import Distribuidor, DistribuidorCreate, User
from database import get_session
from auth.dependencies import get_current_user

router = APIRouter(prefix="/distribuidores", tags=["Distribuidores"])


@router.post("/", response_model=Distribuidor)
def create_distribuidor(
    distribuidor: DistribuidorCreate,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    if current_user.tipo not in ["admin", "distribuidor"]:
        raise HTTPException(status_code=403, detail="Acesso restrito a distribuidores")

    if current_user.ativo:
        raise HTTPException(status_code=400, detail="Usuário já possui um distribuidor cadastrado")

    novo_distribuidor = Distribuidor(
        nome=distribuidor.nome,
        cnpj=distribuidor.cnpj,
        contato=distribuidor.contato,
        id_usuario=current_user.id
    )
    session.add(novo_distribuidor)

    user = session.get(User, current_user.id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    user.ativo = True
    session.add(user)

    session.commit()
    session.refresh(novo_distribuidor)
    session.refresh(user)

    return novo_distribuidor


@router.get("/", response_model=List[Distribuidor])
def list_distribuidores(
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    if current_user.tipo not in ["admin", "distribuidor"]:
        raise HTTPException(status_code=403, detail="Acesso restrito a distribuidores")
    
    if not current_user.ativo:
        raise HTTPException(status_code=403, detail="Finalize seu cadastro")

    if current_user.tipo == "distribuidor":
        distribuidores = session.exec(
            select(Distribuidor).where(Distribuidor.id_usuario == current_user.id)
        ).all()
    else:
        distribuidores = session.exec(select(Distribuidor)).all()
    
    return distribuidores


@router.get("/{distribuidor_id}", response_model=Distribuidor)
def get_distribuidor(
    distribuidor_id: int,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    if current_user.tipo not in ["admin", "distribuidor"]:
        raise HTTPException(status_code=403, detail="Acesso restrito a distribuidores")
    
    if not current_user.ativo:
        raise HTTPException(status_code=403, detail="Finalize seu cadastro")

    distribuidor = session.get(Distribuidor, distribuidor_id)
    if not distribuidor:
        raise HTTPException(status_code=404, detail="Distribuidor não encontrado")

    if current_user.tipo == "distribuidor" and distribuidor.id_usuario != current_user.id:
        raise HTTPException(status_code=403, detail="Você só pode visualizar seus próprios dados")

    return distribuidor


@router.put("/{distribuidor_id}", response_model=Distribuidor)
def update_distribuidor(
    distribuidor_id: int,
    distribuidor: Distribuidor,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    if current_user.tipo not in ["admin", "distribuidor"]:
        raise HTTPException(status_code=403, detail="Acesso restrito a distribuidores")
    
    if not current_user.ativo:
        raise HTTPException(status_code=403, detail="Finalize seu cadastro")

    db_distribuidor = session.get(Distribuidor, distribuidor_id)
    if not db_distribuidor:
        raise HTTPException(status_code=404, detail="Distribuidor não encontrado")

    if current_user.tipo == "distribuidor" and db_distribuidor.id_usuario != current_user.id:
        raise HTTPException(status_code=403, detail="Você só pode alterar seus próprios dados")

    distribuidor_data = distribuidor.model_dump(exclude_unset=True, exclude={"id_distribuidor"})
    for key, value in distribuidor_data.items():
        setattr(db_distribuidor, key, value)

    session.add(db_distribuidor)
    session.commit()
    session.refresh(db_distribuidor)
    return db_distribuidor


@router.delete("/{distribuidor_id}")
def delete_distribuidor(
    distribuidor_id: int,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    if current_user.tipo not in ["admin", "distribuidor"]:
        raise HTTPException(status_code=403, detail="Acesso restrito a distribuidores")
    
    if not current_user.ativo:
        raise HTTPException(status_code=403, detail="Finalize seu cadastro")

    distribuidor = session.get(Distribuidor, distribuidor_id)
    if not distribuidor:
        raise HTTPException(status_code=404, detail="Distribuidor não encontrado")

    if current_user.tipo == "distribuidor" and distribuidor.id_usuario != current_user.id:
        raise HTTPException(status_code=403, detail="Você só pode deletar seu próprio registro")

    session.delete(distribuidor)
    session.commit()
    return {"message": "Distribuidor deletado com sucesso"}
