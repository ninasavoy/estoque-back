from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional

class Farmaceutica(SQLModel, table=True):
    id_farmaceutica: Optional[int] = Field(default=None, primary_key=True)
    nome: str
    cnpj: str
    contato: str

    medicamentos: List["Medicamento"] = Relationship(back_populates="farmaceutica")