from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional

class SUS(SQLModel, table=True):
    id_sus: Optional[int] = Field(default=None, primary_key=True)
    regiao: str
    gestor_responsavel: str

    ubs_list: List["UBS"] = Relationship(back_populates="sus")