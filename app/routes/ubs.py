from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from typing import List
from auth.dependencies import get_current_user
from models import SUS, UBS, User
from database import get_session

router = APIRouter(prefix="/ubs", tags=["UBS"])


@router.post("/", response_model=UBS)
def create_ubs(
    ubs: UBS,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    if current_user.ativo:
        raise HTTPException(status_code=400, detail="Usuário já possui uma UBS cadastrada")

    nova_ubs = UBS(
        nome=ubs.nome,
        contato=ubs.contato,
        endereco=ubs.endereco,
        id_sus=ubs.id_sus,
        id_usuario=current_user.id
    )
    session.add(nova_ubs)

    user = session.get(User, current_user.id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    user.ativo = True
    session.add(user)

    session.commit()
    session.refresh(nova_ubs)
    session.refresh(user)

    return nova_ubs


@router.get("/", response_model=List[UBS])
def list_ubs(
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    if current_user.tipo not in ["admin", "sus", "ubs"]:
        raise HTTPException(status_code=403, detail="Acesso restrito")

    if current_user.tipo == "admin":
        return session.exec(select(UBS)).all()

    if current_user.tipo == "sus":
        sus = session.exec(
            select(SUS).where(SUS.id_usuario == current_user.id)
        ).first()
        if not sus:
            raise HTTPException(status_code=404, detail="SUS não encontrado")
        return session.exec(select(UBS).where(UBS.id_sus == sus.id_sus)).all()

    return session.exec(select(UBS).where(UBS.id_usuario == current_user.id)).all()


@router.get("/{ubs_id}", response_model=UBS)
def get_ubs(
    ubs_id: int,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    ubs = session.get(UBS, ubs_id)
    if not ubs:
        raise HTTPException(status_code=404, detail="UBS não encontrada")

    if current_user.tipo not in ["admin", "sus", "ubs"]:
        raise HTTPException(status_code=403, detail="Acesso restrito")

    if current_user.tipo == "sus":
        sus = session.exec(
            select(SUS).where(SUS.id_usuario == current_user.id)
        ).first()
        if not sus or ubs.id_sus != sus.id_sus:
            raise HTTPException(status_code=403, detail="Você não pode acessar esta UBS")

    if current_user.tipo == "ubs" and ubs.id_usuario != current_user.id:
        raise HTTPException(status_code=403, detail="Acesso negado à UBS especificada")

    return ubs


@router.put("/{ubs_id}", response_model=UBS)
def update_ubs(
    ubs_id: int,
    ubs: UBS,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    db_ubs = session.get(UBS, ubs_id)
    if not db_ubs:
        raise HTTPException(status_code=404, detail="UBS não encontrada")

    if current_user.tipo not in ["admin", "sus", "ubs"]:
        raise HTTPException(status_code=403, detail="Acesso restrito")

    if current_user.tipo == "ubs" and db_ubs.id_usuario != current_user.id:
        raise HTTPException(status_code=403, detail="Você só pode atualizar sua própria UBS")

    if current_user.tipo == "sus":
        sus = session.exec(
            select(SUS).where(SUS.id_usuario == current_user.id)
        ).first()
        if not sus or db_ubs.id_sus != sus.id_sus:
            raise HTTPException(status_code=403, detail="Você não pode atualizar esta UBS")

    ubs_data = ubs.model_dump(exclude_unset=True, exclude={"id_ubs"})
    for key, value in ubs_data.items():
        setattr(db_ubs, key, value)

    session.add(db_ubs)
    session.commit()
    session.refresh(db_ubs)
    return db_ubs


@router.delete("/{ubs_id}")
def delete_ubs(
    ubs_id: int,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    ubs = session.get(UBS, ubs_id)
    if not ubs:
        raise HTTPException(status_code=404, detail="UBS não encontrada")

    # Admin pode deletar qualquer uma
    # SUS pode deletar UBS da sua região
    # UBS só pode deletar a própria conta
    if current_user.tipo not in ["admin", "sus", "ubs"]:
        raise HTTPException(status_code=403, detail="Acesso restrito")

    if current_user.tipo == "sus":
        sus = session.exec(
            select(SUS).where(SUS.id_usuario == current_user.id)
        ).first()
        if not sus or ubs.id_sus != sus.id_sus:
            raise HTTPException(status_code=403, detail="Você não pode deletar esta UBS")

    if current_user.tipo == "ubs" and ubs.id_usuario != current_user.id:
        raise HTTPException(status_code=403, detail="Você só pode deletar sua própria UBS")

    session.delete(ubs)
    session.commit()
    return {"message": "UBS deletada com sucesso"}