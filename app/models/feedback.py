from sqlmodel import SQLModel, Field, Relationship
from datetime import date
from typing import Optional

class Feedback(SQLModel, table=True):
    id_feedback: Optional[int] = Field(default=None, primary_key=True)
    id_paciente: int = Field(foreign_key="paciente.id_paciente")
    id_medicamento: int = Field(foreign_key="medicamento.id_medicamento")
    comentario: str
    data: date
    tipo: str

    paciente: Optional["Paciente"] = Relationship(back_populates="feedbacks")
    medicamento: Optional["Medicamento"] = Relationship(back_populates="feedbacks")
