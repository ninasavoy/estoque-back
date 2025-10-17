from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import date

class Movimentacao(SQLModel, table=True):
    id_mov: Optional[int] = Field(default=None, primary_key=True)
    id_lote: int = Field(foreign_key="lote.id_lote")
    tipo_origem: str
    origem_id: int
    tipo_destino: str
    destino_id: int
    data_envio: Optional[date] = None
    data_recebimento: Optional[date] = None
    status: str

    lote: Optional["Lote"] = Relationship(back_populates="movimentacoes")
