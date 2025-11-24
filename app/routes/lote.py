from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from typing import List
from datetime import datetime
from models import Lote, LoteBase
from database import get_session
from auth.dependencies import get_current_user
from models import User, Farmaceutica, Medicamento

router = APIRouter(prefix="/lotes", tags=["Lotes"])



# -------------------------
# Criar lote
# -------------------------
@router.post("/", response_model=Lote)
def create_lote(
    lote: LoteBase, 
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    if current_user.tipo not in ["admin", "farmaceutica"]:
        raise HTTPException(status_code=403, detail="Acesso restrito a administradores e farmacêuticas.")

    if current_user.tipo == "farmaceutica":
        farmaceutica = session.exec(
            select(Farmaceutica).where(Farmaceutica.id_usuario == current_user.id)
        ).first()
        if not farmaceutica:
            raise HTTPException(status_code=404, detail="Farmacêutica não encontrada.")

        medicamento = session.get(Medicamento, lote.id_medicamento)
        if not medicamento:
            raise HTTPException(status_code=404, detail="Medicamento não encontrado.")
        if medicamento.id_farmaceutica != farmaceutica.id_farmaceutica:
            raise HTTPException(status_code=403, detail="Você não pode criar lotes para medicamentos de outras farmacêuticas.")

    # Converte LoteBase em Lote (model de tabela)
    db_lote = Lote.model_validate(lote)
    
    session.add(db_lote)
    session.commit()
    session.refresh(db_lote)
    return db_lote


# -------------------------
# Listar todos os lotes
# -------------------------
@router.get("/", response_model=List[Lote])
def list_lotes(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    if current_user.tipo == "admin":
        return session.exec(select(Lote)).all()

    elif current_user.tipo == "farmaceutica":
        farmaceutica = session.exec(
            select(Farmaceutica).where(Farmaceutica.id_usuario == current_user.id)
        ).first()
        if not farmaceutica:
            raise HTTPException(status_code=404, detail="Farmacêutica não encontrada.")

        query = (
            select(Lote)
            .join(Medicamento)
            .where(Medicamento.id_farmaceutica == farmaceutica.id_farmaceutica)
        )
        return session.exec(query).all()

    else:
        raise HTTPException(status_code=403, detail="Acesso restrito a administradores e farmacêuticas.")
    

@router.get("/vencidos/", response_model=List[Lote])
def list_lotes_vencidos(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    now = datetime.now()

    # Admin vê tudo
    if current_user.tipo == "admin":
        query = select(Lote).where(Lote.data_vencimento < now)
        return session.exec(query).all()

    # Farmacêutica vê só os lotes dos seus medicamentos
    if current_user.tipo == "farmaceutica":
        farmaceutica = session.exec(
            select(Farmaceutica).where(Farmaceutica.id_usuario == current_user.id)
        ).first()
        if not farmaceutica:
            raise HTTPException(status_code=404, detail="Farmacêutica não encontrada.")

        query = (
            select(Lote)
            .join(Medicamento)
            .where(
                Medicamento.id_farmaceutica == farmaceutica.id_farmaceutica,
                Lote.data_vencimento < now
            )
        )
        return session.exec(query).all()


# -------------------------
# Obter lote por ID
# -------------------------
@router.get("/{lote_id}", response_model=Lote)
def get_lote(
    lote_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    lote = session.get(Lote, lote_id)
    if not lote:
        raise HTTPException(status_code=404, detail="Lote não encontrado.")

    if current_user.tipo == "admin":
        return lote

    if current_user.tipo == "farmaceutica":
        farmaceutica = session.exec(
            select(Farmaceutica).where(Farmaceutica.id_usuario == current_user.id)
        ).first()
        medicamento = session.get(Medicamento, lote.id_medicamento)
        if medicamento.id_farmaceutica != farmaceutica.id_farmaceutica:
            raise HTTPException(status_code=403, detail="Acesso negado a este lote.")
        return lote

    raise HTTPException(status_code=403, detail="Acesso restrito a administradores e farmacêuticas.")


# -------------------------
# Atualizar lote
# -------------------------
@router.put("/{lote_id}", response_model=Lote)
def update_lote(
    lote_id: int,
    lote: LoteBase,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    db_lote = session.get(Lote, lote_id)
    if not db_lote:
        raise HTTPException(status_code=404, detail="Lote não encontrado.")

    # Admin pode editar tudo
    if current_user.tipo == "admin":
        pass
    # Farmacêutica pode editar só seus lotes
    elif current_user.tipo == "farmaceutica":
        farmaceutica = session.exec(
            select(Farmaceutica).where(Farmaceutica.id_usuario == current_user.id)
        ).first()
        medicamento = session.get(Medicamento, db_lote.id_medicamento)
        if medicamento.id_farmaceutica != farmaceutica.id_farmaceutica:
            raise HTTPException(status_code=403, detail="Você não pode editar lotes de outras farmacêuticas.")
    else:
        raise HTTPException(status_code=403, detail="Acesso negado.")

    lote_data = lote.model_dump(exclude_unset=True, exclude={"id_lote"})
    for key, value in lote_data.items():
        setattr(db_lote, key, value)

    session.add(db_lote)
    session.commit()
    session.refresh(db_lote)
    return db_lote


# -------------------------
# Deletar lote
# -------------------------
@router.delete("/{lote_id}")
def delete_lote(
    lote_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    lote = session.get(Lote, lote_id)
    if not lote:
        raise HTTPException(status_code=404, detail="Lote não encontrado.")

    if current_user.tipo == "admin":
        pass
    elif current_user.tipo == "farmaceutica":
        farmaceutica = session.exec(
            select(Farmaceutica).where(Farmaceutica.id_usuario == current_user.id)
        ).first()
        medicamento = session.get(Medicamento, lote.id_medicamento)
        if medicamento.id_farmaceutica != farmaceutica.id_farmaceutica:
            raise HTTPException(status_code=403, detail="Você não pode deletar lotes de outras farmacêuticas.")
    else:
        raise HTTPException(status_code=403, detail="Acesso negado.")

    session.delete(lote)
    session.commit()
    return {"message": "Lote deletado com sucesso"}
