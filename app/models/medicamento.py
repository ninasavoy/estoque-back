from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional
from .farmaceutica import Farmaceutica

class Medicamento(SQLModel, table=True):
    id_medicamento: Optional[int] = Field(default=None, primary_key=True)
    nome: str
    id_farmaceutica: int = Field(foreign_key="farmaceutica.id_farmaceutica")

    farmaceutica: Optional[Farmaceutica] = Relationship(back_populates="medicamentos")
    lotes: List["Lote"] = Relationship(back_populates="medicamento")
    feedbacks: List["Feedback"] = Relationship(back_populates="medicamento")
