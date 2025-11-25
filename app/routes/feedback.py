from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from typing import List
from auth.dependencies import get_current_user
from models import Farmaceutica, Feedback, FeedbackCreate, FeedbackUpdate, Medicamento, Paciente
from database import get_session
from datetime import datetime


router = APIRouter(prefix="/feedbacks", tags=["Feedbacks"])


# CREATE ---------------------------------------------------------
@router.post("/", response_model=Feedback)
def create_feedback(
    feedback: FeedbackCreate,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    # Apenas pacientes podem criar feedback
    if current_user.tipo != "paciente":
        raise HTTPException(403, "Somente pacientes podem criar feedbacks.")
    
    if not current_user.ativo:
        raise HTTPException(status_code=403, detail="Finalize seu cadastro")

    paciente = session.exec(
        select(Paciente).where(Paciente.id_usuario == current_user.id)
    ).first()
    
    if not paciente:
        raise HTTPException(404, "Paciente não encontrado")

    feedback_obj = Feedback(
        **feedback.model_dump(),
        id_paciente=paciente.id_paciente
    )

    session.add(feedback_obj)
    session.commit()
    session.refresh(feedback_obj)
    return feedback_obj


# READ -----------------------------------------------------------
@router.get("/", response_model=List[Feedback])
def list_feedbacks(
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    if not current_user.ativo:
        raise HTTPException(status_code=403, detail="Finalize seu cadastro")
    
    if current_user.tipo == "admin":
        return session.exec(select(Feedback)).all()

    if current_user.tipo == "farmaceutica":
        farmaceutica = session.exec(
            select(Farmaceutica).where(Farmaceutica.id_usuario == current_user.id)
        ).first()

        if not farmaceutica:
            raise HTTPException(404, "Farmacêutica não encontrada")

        medicamentos_ids = session.exec(
            select(Medicamento.id_medicamento).where(
                Medicamento.id_farmaceutica == farmaceutica.id_farmaceutica
            )
        ).all()

        return session.exec(
            select(Feedback).where(Feedback.id_medicamento.in_(medicamentos_ids))
        ).all()

    if current_user.tipo == "paciente":
        paciente = session.exec(
            select(Paciente).where(Paciente.id_usuario == current_user.id)
        ).first()
        
        if not paciente:
            raise HTTPException(404, "Paciente não encontrado")
        
        return session.exec(
            select(Feedback).where(Feedback.id_paciente == paciente.id_paciente)
        ).all()

    raise HTTPException(403, "Você não tem permissão para ver feedbacks.")


@router.get("/{feedback_id}", response_model=Feedback)
def get_feedback(
    feedback_id: int,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    if not current_user.ativo:
        raise HTTPException(status_code=403, detail="Finalize seu cadastro")
    
    feedback = session.get(Feedback, feedback_id)
    if not feedback:
        raise HTTPException(404, "Feedback não encontrado")

    # ADMIN pode ver tudo
    if current_user.tipo == "admin":
        return feedback

    # PACIENTE só vê seus próprios
    if current_user.tipo == "paciente":
        paciente = session.exec(
            select(Paciente).where(Paciente.id_usuario == current_user.id)
        ).first()
        
        if not paciente:
            raise HTTPException(404, "Paciente não encontrado")
        
        if feedback.id_paciente != paciente.id_paciente:
            raise HTTPException(403, "Você não pode acessar este feedback")
        return feedback

    # FARMACÊUTICA só vê feedbacks dos seus medicamentos
    if current_user.tipo == "farmaceutica":
        farmaceutica = session.exec(
            select(Farmaceutica).where(Farmaceutica.id_usuario == current_user.id)
        ).first()
        
        if not farmaceutica:
            raise HTTPException(404, "Farmacêutica não encontrada")

        medicamento = session.get(Medicamento, feedback.id_medicamento)
        
        if not medicamento:
            raise HTTPException(404, "Medicamento não encontrado")

        if medicamento.id_farmaceutica != farmaceutica.id_farmaceutica:
            raise HTTPException(403, "Você não tem permissão para ver este feedback")

        return feedback

    raise HTTPException(403, "Você não tem permissão")


# UPDATE ---------------------------------------------------------
@router.put("/{feedback_id}", response_model=Feedback)
def update_feedback(
    feedback_id: int,
    feedback: FeedbackUpdate,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    if not current_user.ativo:
        raise HTTPException(status_code=403, detail="Finalize seu cadastro")
    
    db_feedback = session.get(Feedback, feedback_id)
    if not db_feedback:
        raise HTTPException(404, "Feedback não encontrado")

    # Somente PACIENTE dono do feedback pode alterar
    if current_user.tipo != "paciente":
        raise HTTPException(403, "Somente pacientes podem alterar feedbacks")

    paciente = session.exec(
        select(Paciente).where(Paciente.id_usuario == current_user.id)
    ).first()
    
    if not paciente:
        raise HTTPException(404, "Paciente não encontrado")

    if db_feedback.id_paciente != paciente.id_paciente:
        raise HTTPException(403, "Você só pode alterar seus próprios feedbacks")

    feedback_data = feedback.model_dump(exclude_unset=True)
    for key, value in feedback_data.items():
        setattr(db_feedback, key, value)

    session.add(db_feedback)
    session.commit()
    session.refresh(db_feedback)
    return db_feedback


# DELETE ---------------------------------------------------------
@router.delete("/{feedback_id}")
def delete_feedback(
    feedback_id: int,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    if not current_user.ativo:
        raise HTTPException(status_code=403, detail="Finalize seu cadastro") 
    
    feedback = session.get(Feedback, feedback_id)
    if not feedback:
        raise HTTPException(404, "Feedback não encontrado")

    # Somente PACIENTE dono pode deletar
    if current_user.tipo != "paciente":
        raise HTTPException(403, "Somente pacientes podem deletar feedbacks")

    paciente = session.exec(
        select(Paciente).where(Paciente.id_usuario == current_user.id)
    ).first()
    
    if not paciente:
        raise HTTPException(404, "Paciente não encontrado")

    if feedback.id_paciente != paciente.id_paciente:
        raise HTTPException(403, "Você só pode deletar seus próprios feedbacks")

    session.delete(feedback)
    session.commit()
    return {"message": "Feedback deletado com sucesso"}