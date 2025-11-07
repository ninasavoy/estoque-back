from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from typing import List
from auth.dependencies import get_current_user
from models import Farmaceutica, FarmaceuticaCreate, User
from database import get_session

router = APIRouter(prefix="/farmaceuticas", tags=["Farmacêuticas"])


@router.post("/", response_model=Farmaceutica)
def create_farmaceutica(farmaceutica: FarmaceuticaCreate, 
                        session: Session = Depends(get_session), 
                        current_user = Depends(get_current_user)):
    
    if current_user.tipo != "farmaceutica" and current_user.tipo != "admin":
        raise HTTPException(status_code=403, detail="Acesso restrito a farmacêuticas")

    if current_user.ativo:
        raise HTTPException(status_code=400, detail="Usuário já possui uma farmacêutica cadastrada")

    nova_farmaceutica = Farmaceutica(
        nome=farmaceutica.nome,
        cnpj=farmaceutica.cnpj,
        contato=farmaceutica.contato,
        id_usuario=current_user.id
    )
    session.add(nova_farmaceutica)

    user = session.get(User, current_user.id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    user.ativo = True
    session.add(user)

    session.commit()

    session.refresh(nova_farmaceutica)
    session.refresh(user)

    return nova_farmaceutica


@router.get("/", response_model=List[Farmaceutica])
def list_farmaceuticas(session: Session = Depends(get_session), current_user = Depends(get_current_user)):
    if current_user.tipo != "farmaceutica" and current_user.tipo != "admin":
        raise HTTPException(status_code=403, detail="Acesso restrito a farmacêuticas")
    
    if current_user.tipo == "farmaceutica":
        farmaceutica = session.exec(
            select(Farmaceutica).where(Farmaceutica.id_usuario == current_user.id)
        ).first()

        if not farmaceutica:
            raise HTTPException(status_code=404, detail="Farmacêutica não encontrada")
        
        return [farmaceutica]
    
    farmaceuticas = session.exec(select(Farmaceutica)).all()
    return farmaceuticas


@router.get("/{farmaceutica_id}", response_model=Farmaceutica)
def get_farmaceutica(farmaceutica_id: int, session: Session = Depends(get_session), current_user = Depends(get_current_user)):
    if current_user.tipo != "farmaceutica" and current_user.tipo != "admin":
        raise HTTPException(status_code=403, detail="Acesso restrito a farmacêuticas")

    farmaceutica = session.get(Farmaceutica, farmaceutica_id)
    if not farmaceutica:
        raise HTTPException(status_code=404, detail="Farmacêutica não encontrada")

    if current_user.tipo == "farmaceutica":
        user_farmaceutica = session.exec(
            select(Farmaceutica).where(Farmaceutica.id_usuario == current_user.id)
        ).first()

        if not user_farmaceutica or user_farmaceutica.id_farmaceutica != farmaceutica_id:
            raise HTTPException(
                status_code=403,
                detail="Você só pode visualizar os dados da sua própria farmacêutica"
            )

    return farmaceutica


@router.put("/{farmaceutica_id}", response_model=Farmaceutica)
def update_farmaceutica(
    farmaceutica_id: int, 
    farmaceutica: Farmaceutica, 
    session: Session = Depends(get_session), 
    current_user = Depends(get_current_user)
):
    if current_user.tipo != "farmaceutica" and current_user.tipo != "admin":
        raise HTTPException(status_code=403, detail="Acesso restrito a farmacêuticas")
    
    db_farmaceutica = session.get(Farmaceutica, farmaceutica_id)
    if not db_farmaceutica:
        raise HTTPException(status_code=404, detail="Farmacêutica não encontrada")

    if current_user.tipo == "farmaceutica":
        user_farmaceutica = session.exec(
            select(Farmaceutica).where(Farmaceutica.id_usuario == current_user.id)
        ).first()

        if not user_farmaceutica or user_farmaceutica.id_farmaceutica != farmaceutica_id:
            raise HTTPException(
                status_code=403,
                detail="Você só pode alterar os dados da sua própria farmacêutica"
            )

    farmaceutica_data = farmaceutica.model_dump(
        exclude_unset=True,
        exclude={"id_farmaceutica"}
    )
    for key, value in farmaceutica_data.items():
        setattr(db_farmaceutica, key, value)

    session.add(db_farmaceutica)
    session.commit()
    session.refresh(db_farmaceutica)

    return db_farmaceutica


@router.delete("/{farmaceutica_id}")
def delete_farmaceutica(farmaceutica_id: int, session: Session = Depends(get_session), current_user = Depends(get_current_user)):
    if current_user.tipo != "farmaceutica" and current_user.tipo != "admin":
        raise HTTPException(status_code=403, detail="Acesso restrito a farmacêuticas")
    farmaceutica = session.get(Farmaceutica, farmaceutica_id)
    if not farmaceutica:
        raise HTTPException(status_code=404, detail="Farmacêutica não encontrada")
    
    if current_user.tipo == "farmaceutica":
        user_farmaceutica = session.exec(
            select(Farmaceutica).where(Farmaceutica.id_usuario == current_user.id)
        ).first()

        if not user_farmaceutica or user_farmaceutica.id_farmaceutica != farmaceutica_id:
            raise HTTPException(
                status_code=403,
                detail="Você só pode deletar a sua própria farmacêutica"
            )
    
    session.delete(farmaceutica)
    session.commit()
    return {"message": "Farmacêutica deletada com sucesso"}