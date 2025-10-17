from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from typing import List
from models import Feedback
from database import get_session

router = APIRouter(prefix="/feedbacks", tags=["Feedbacks"])


@router.post("/", response_model=Feedback)
def create_feedback(feedback: Feedback, session: Session = Depends(get_session)):
    session.add(feedback)
    session.commit()
    session.refresh(feedback)
    return feedback


@router.get("/", response_model=List[Feedback])
def list_feedbacks(session: Session = Depends(get_session)):
    feedbacks = session.exec(select(Feedback)).all()
    return feedbacks


@router.get("/{feedback_id}", response_model=Feedback)
def get_feedback(feedback_id: int, session: Session = Depends(get_session)):
    feedback = session.get(Feedback, feedback_id)
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback não encontrado")
    return feedback


@router.get("/paciente/{paciente_id}", response_model=List[Feedback])
def list_feedbacks_by_paciente(
    paciente_id: int, 
    session: Session = Depends(get_session)
):
    feedbacks = session.exec(
        select(Feedback).where(Feedback.id_paciente == paciente_id)
    ).all()
    return feedbacks


@router.get("/medicamento/{medicamento_id}", response_model=List[Feedback])
def list_feedbacks_by_medicamento(
    medicamento_id: int, 
    session: Session = Depends(get_session)
):
    feedbacks = session.exec(
        select(Feedback).where(Feedback.id_medicamento == medicamento_id)
    ).all()
    return feedbacks


@router.get("/tipo/{tipo}", response_model=List[Feedback])
def list_feedbacks_by_tipo(
    tipo: str, 
    session: Session = Depends(get_session)
):
    feedbacks = session.exec(
        select(Feedback).where(Feedback.tipo == tipo)
    ).all()
    return feedbacks


@router.put("/{feedback_id}", response_model=Feedback)
def update_feedback(
    feedback_id: int, 
    feedback: Feedback, 
    session: Session = Depends(get_session)
):
    db_feedback = session.get(Feedback, feedback_id)
    if not db_feedback:
        raise HTTPException(status_code=404, detail="Feedback não encontrado")
    
    feedback_data = feedback.model_dump(exclude_unset=True, exclude={"id_feedback"})
    for key, value in feedback_data.items():
        setattr(db_feedback, key, value)
    
    session.add(db_feedback)
    session.commit()
    session.refresh(db_feedback)
    return db_feedback


@router.delete("/{feedback_id}")
def delete_feedback(feedback_id: int, session: Session = Depends(get_session)):
    feedback = session.get(Feedback, feedback_id)
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback não encontrado")
    
    session.delete(feedback)
    session.commit()
    return {"message": "Feedback deletado com sucesso"}