from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional

class Paciente(SQLModel, table=True):
    id_paciente: Optional[int] = Field(default=None, primary_key=True)
    nome: str
    cpf: str
    contato: str
    id_ubs: int = Field(foreign_key="ubs.id_ubs")

    ubs: Optional["UBS"] = Relationship(back_populates="pacientes")
    feedbacks: List["Feedback"] = Relationship(back_populates="paciente")
