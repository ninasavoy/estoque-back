from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from typing import List
from auth.dependencies import get_current_user
from models import Paciente, UBS, SUS, PacienteCreate, User
from database import get_session

router = APIRouter(prefix="/pacientes", tags=["Pacientes"])


@router.post("/", response_model=Paciente)
def create_paciente(
    paciente: PacienteCreate,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    if current_user.tipo not in ["admin","paciente"]:
        raise HTTPException(status_code=403, detail="Acesso restrito a UBS e administradores")

    if current_user.ativo:
        raise HTTPException(status_code=400, detail="Usuário já possui um cadastro de paciente")

    novo_paciente = Paciente(
        nome=paciente.nome,
        sobrenome=paciente.sobrenome,
        cpf=paciente.cpf,
        contato=paciente.contato,
        id_ubs=paciente.id_ubs,
        id_usuario=current_user.id
    )
    session.add(novo_paciente)

    user = session.get(User, current_user.id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    user.ativo = True
    session.add(user)

    session.commit()
    session.refresh(novo_paciente)
    session.refresh(user)

    return novo_paciente


@router.get("/", response_model=List[Paciente])
def list_pacientes(
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    if current_user.tipo not in ["admin","sus", "ubs", "paciente"]:
        raise HTTPException(status_code=403, detail="Acesso restrito a UBS, SUS, pacientes e administradores")

    if current_user.tipo == "admin":
        return session.exec(select(Paciente)).all()

    if current_user.tipo == "sus":
        sus = session.exec(
            select(SUS).where(SUS.id_usuario == current_user.id)
        ).first()
        if not sus:
            raise HTTPException(status_code=404, detail="SUS não encontrado")

        ubs_ids = session.exec(
            select(UBS.id_ubs).where(UBS.id_sus == sus.id_sus)
        ).all()

        return session.exec(
            select(Paciente).where(Paciente.id_ubs.in_(ubs_ids))
        ).all()

    if current_user.tipo == "ubs":
        ubs = session.exec(
            select(UBS).where(UBS.id_usuario == current_user.id)
        ).first()
        if not ubs:
            raise HTTPException(status_code=404, detail="UBS não encontrada")

        return session.exec(
            select(Paciente).where(Paciente.id_ubs == ubs.id_ubs)
        ).all()

    if current_user.tipo == "paciente":
        return session.exec(
            select(Paciente).where(Paciente.id_usuario == current_user.id)
        ).all()

    raise HTTPException(status_code=403, detail="Acesso negado")


@router.get("/{paciente_id}", response_model=Paciente)
def get_paciente(
    paciente_id: int,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    if current_user.tipo not in ["admin","sus", "ubs", "paciente"]:
        raise HTTPException(status_code=403, detail="Acesso restrito a UBS, SUS, pacientes e administradores")
    
    paciente = session.get(Paciente, paciente_id)
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente não encontrado")

    if current_user.tipo == "admin":
        return paciente

    if current_user.tipo == "sus":
        sus = session.exec(
            select(SUS).where(SUS.id_usuario == current_user.id)
        ).first()
        if not sus:
            raise HTTPException(status_code=404, detail="SUS não encontrado")

        ubs = session.get(UBS, paciente.id_ubs)
        if not ubs or ubs.id_sus != sus.id_sus:
            raise HTTPException(status_code=403, detail="Acesso negado")

    if current_user.tipo == "ubs":
        ubs = session.exec(
            select(UBS).where(UBS.id_usuario == current_user.id)
        ).first()
        if not ubs or paciente.id_ubs != ubs.id_ubs:
            raise HTTPException(status_code=403, detail="Acesso negado")

    if current_user.tipo == "paciente" and paciente.id_usuario != current_user.id:
        raise HTTPException(status_code=403, detail="Você só pode ver o próprio cadastro")

    return paciente


@router.put("/{paciente_id}", response_model=Paciente)
def update_paciente(
    paciente_id: int,
    paciente: Paciente,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    db_paciente = session.get(Paciente, paciente_id)
    if not db_paciente:
        raise HTTPException(status_code=404, detail="Paciente não encontrado")

    if current_user.tipo not in ["admin", "ubs", "paciente"]:
        raise HTTPException(status_code=403, detail="Acesso negado")

    if current_user.tipo == "ubs":
        ubs = session.exec(
            select(UBS).where(UBS.id_usuario == current_user.id)
        ).first()
        if not ubs or db_paciente.id_ubs != ubs.id_ubs:
            raise HTTPException(status_code=403, detail="Você não pode atualizar este paciente")

    if current_user.tipo == "paciente" and db_paciente.id_usuario != current_user.id:
        raise HTTPException(status_code=403, detail="Você só pode atualizar seu próprio cadastro")

    paciente_data = paciente.model_dump(exclude_unset=True, exclude={"id_paciente"})
    for key, value in paciente_data.items():
        setattr(db_paciente, key, value)

    session.add(db_paciente)
    session.commit()
    session.refresh(db_paciente)
    return db_paciente


@router.delete("/{paciente_id}")
def delete_paciente(
    paciente_id: int,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    paciente = session.get(Paciente, paciente_id)
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente não encontrado")

    if current_user.tipo not in ["admin", "ubs", "paciente"]:
        raise HTTPException(status_code=403, detail="Acesso negado")

    if current_user.tipo == "ubs":
        ubs = session.exec(
            select(UBS).where(UBS.id_usuario == current_user.id)
        ).first()
        if not ubs or paciente.id_ubs != ubs.id_ubs:
            raise HTTPException(status_code=403, detail="Você não pode deletar este paciente")

    if current_user.tipo == "paciente" and paciente.id_usuario != current_user.id:
        raise HTTPException(status_code=403, detail="Você só pode deletar seu próprio cadastro")

    session.delete(paciente)
    session.commit()
    return {"message": "Paciente deletado com sucesso"}