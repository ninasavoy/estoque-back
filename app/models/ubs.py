from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional

class UBS(SQLModel, table=True):
    id_ubs: Optional[int] = Field(default=None, primary_key=True)
    nome: str
    endereco: str
    id_sus: int = Field(foreign_key="sus.id_sus")

    sus: Optional[SUS] = Relationship(back_populates="ubs_list")
    pacientes: List["Paciente"] = Relationship(back_populates="ubs")