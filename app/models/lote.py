from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional
from datetime import date

class Lote(SQLModel, table=True):
    id_lote: Optional[int] = Field(default=None, primary_key=True)
    id_medicamento: int = Field(foreign_key="medicamento.id_medicamento")
    codigo_lote: str
    data_fabricacao: date
    data_validade: date
    quantidade_inicial: int

    medicamento: Optional["Medicamento"] = Relationship(back_populates="lotes")
    movimentacoes: List["Movimentacao"] = Relationship(back_populates="lote")
