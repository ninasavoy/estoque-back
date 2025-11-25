from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from typing import List
from auth.dependencies import get_current_user
from models import SUS, SUSCreate, User
from database import get_session

router = APIRouter(prefix="/sus", tags=["SUS"])


@router.post("/", response_model=SUS)
def create_sus(
    sus: SUSCreate,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    if current_user.tipo not in ["admin", "sus"]:
        raise HTTPException(status_code=403, detail="Acesso restrito a administradores e SUS")

    if current_user.ativo:
        raise HTTPException(status_code=400, detail="Usuário já possui um cadastro de SUS")

    novo_sus = SUS(
        regiao=sus.regiao,
        contato_gestor=sus.contato_gestor,
        nome_gestor=sus.nome_gestor,
        id_usuario=current_user.id
    )
    session.add(novo_sus)

    user = session.get(User, current_user.id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    user.ativo = True
    session.add(user)

    session.commit()
    session.refresh(novo_sus)
    session.refresh(user)

    return novo_sus


@router.get("/", response_model=List[SUS])
def list_sus(
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    if current_user.tipo not in ["admin", "sus"]:
        raise HTTPException(status_code=403, detail="Acesso restrito a administradores e SUS")
    
    if not current_user.ativo:
        raise HTTPException(status_code=403, detail="Finalize seu cadastro")

    if current_user.tipo == "admin":
        sus_list = session.exec(select(SUS)).all()
        return sus_list

    sus_list = session.exec(
        select(SUS).where(SUS.id_usuario == current_user.id)
    ).all()

    return sus_list


@router.get("/{sus_id}", response_model=SUS)
def get_sus(
    sus_id: int,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    if current_user.tipo not in ["admin", "sus"]:
        raise HTTPException(status_code=403, detail="Acesso restrito a administradores e SUS")
    
    if not current_user.ativo:
        raise HTTPException(status_code=403, detail="Finalize seu cadastro")

    sus = session.get(SUS, sus_id)
    if not sus:
        raise HTTPException(status_code=404, detail="SUS não encontrado")

    if current_user.tipo == "sus" and sus.id_usuario != current_user.id:
        raise HTTPException(status_code=403, detail="Você só pode visualizar seu próprio registro")

    return sus


@router.put("/{sus_id}", response_model=SUS)
def update_sus(
    sus_id: int,
    sus: SUS,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    if current_user.tipo not in ["admin", "sus"]:
        raise HTTPException(status_code=403, detail="Acesso restrito a administradores e SUS")
    
    if not current_user.ativo:
        raise HTTPException(status_code=403, detail="Finalize seu cadastro")

    db_sus = session.get(SUS, sus_id)
    if not db_sus:
        raise HTTPException(status_code=404, detail="SUS não encontrado")

    if current_user.tipo == "sus" and db_sus.id_usuario != current_user.id:
        raise HTTPException(status_code=403, detail="Você só pode alterar seu próprio registro")

    sus_data = sus.model_dump(exclude_unset=True, exclude={"id_sus"})
    for key, value in sus_data.items():
        setattr(db_sus, key, value)

    session.add(db_sus)
    session.commit()
    session.refresh(db_sus)
    return db_sus


@router.delete("/{sus_id}")
def delete_sus(
    sus_id: int,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    if current_user.tipo not in ["admin", "sus"]:
        raise HTTPException(status_code=403, detail="Acesso restrito a administradores e SUS")
    
    if not current_user.ativo:
        raise HTTPException(status_code=403, detail="Finalize seu cadastro")

    sus = session.get(SUS, sus_id)
    if not sus:
        raise HTTPException(status_code=404, detail="SUS não encontrado")

    if current_user.tipo == "sus" and sus.id_usuario != current_user.id:
        raise HTTPException(status_code=403, detail="Você só pode deletar seu próprio registro")

    session.delete(sus)
    session.commit()
    return {"message": "SUS deletado com sucesso"}