from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime

# -------------------------
# USUÁRIOS PARA LOGIN
# -------------------------
class UserBase(SQLModel):
    nome: str
    email: str
    senha_hash: str
    tipo: str  # 'farmaceutica', 'distribuidor', 'sus', 'ubs', 'paciente'


class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)


# -------------------------
# FARMACÊUTICA / MEDICAMENTOS / LOTES
# -------------------------
class Farmaceutica(SQLModel, table=True):
    id_farmaceutica: Optional[int] = Field(default=None, primary_key=True)
    nome: str
    cnpj: str
    contato: str

    medicamentos: List["Medicamento"] = Relationship(back_populates="farmaceutica")


class Medicamento(SQLModel, table=True):
    id_medicamento: Optional[int] = Field(default=None, primary_key=True)
    nome: str
    ingestao: Optional[str] = None
    dosagem: Optional[str] = None
    id_farmaceutica: Optional[int] = Field(default=None, foreign_key="farmaceutica.id_farmaceutica")

    farmaceutica: Optional[Farmaceutica] = Relationship(back_populates="medicamentos")
    lotes: List["Lote"] = Relationship(back_populates="medicamento")


class Lote(SQLModel, table=True):
    id_lote: Optional[int] = Field(default=None, primary_key=True)
    codigo_lote: str
    data_fabricacao: datetime
    data_vencimento: datetime
    quantidade: int
    id_medicamento: Optional[int] = Field(default=None, foreign_key="medicamento.id_medicamento")

    medicamento: Optional[Medicamento] = Relationship(back_populates="lotes")


# -------------------------
# DISTRIBUIDOR
# -------------------------
class Distribuidor(SQLModel, table=True):
    id_distribuidor: Optional[int] = Field(default=None, primary_key=True)
    nome: str
    localizacao: str
    contato: str


# -------------------------
# GESTOR
# -------------------------
class Gestor(SQLModel, table=True):
    id_gestor: Optional[int] = Field(default=None, primary_key=True)
    nome: str
    sobrenome: str
    cpf: str
    contato: str


# -------------------------
# SUS
# -------------------------
class SUS(SQLModel, table=True):
    id_sus: Optional[int] = Field(default=None, primary_key=True)
    regiao: str
    id_gestor: Optional[int] = Field(default=None, foreign_key="gestor.id_gestor")

    gestor: Optional[Gestor] = Relationship()
    ubs: List["UBS"] = Relationship(back_populates="sus")


# -------------------------
# UBS
# -------------------------
class UBS(SQLModel, table=True):
    id_ubs: Optional[int] = Field(default=None, primary_key=True)
    nome: str
    contato: str
    endereco: str
    id_sus: Optional[int] = Field(default=None, foreign_key="sus.id_sus")

    sus: Optional[SUS] = Relationship(back_populates="ubs")
    pacientes: List["Paciente"] = Relationship(back_populates="ubs")


# -------------------------
# PACIENTE
# -------------------------
class Paciente(SQLModel, table=True):
    id_paciente: Optional[int] = Field(default=None, primary_key=True)
    nome: str
    sobrenome: str
    cpf: str
    contato: str
    id_ubs: Optional[int] = Field(default=None, foreign_key="ubs.id_ubs")

    ubs: Optional[UBS] = Relationship(back_populates="pacientes")


# -------------------------
# MOVIMENTAÇÕES
# -------------------------
class DistribuidorParaSUS(SQLModel, table=True):
    id_dps: Optional[int] = Field(default=None, primary_key=True)
    id_distribuidor: int = Field(foreign_key="distribuidor.id_distribuidor")
    id_sus: int = Field(foreign_key="sus.id_sus")
    id_lote: int = Field(foreign_key="lote.id_lote")
    data_envio: datetime
    data_recebimento: Optional[datetime] = None
    status: str


class SUSParaUBS(SQLModel, table=True):
    id_spu: Optional[int] = Field(default=None, primary_key=True)
    id_sus: int = Field(foreign_key="sus.id_sus")
    id_ubs: int = Field(foreign_key="ubs.id_ubs")
    id_lote: int = Field(foreign_key="lote.id_lote")
    data_envio: datetime
    data_recebimento: Optional[datetime] = None
    status: str


class UBSParaPaciente(SQLModel, table=True):
    id_upp: Optional[int] = Field(default=None, primary_key=True)
    id_ubs: int = Field(foreign_key="ubs.id_ubs")
    id_paciente: int = Field(foreign_key="paciente.id_paciente")
    id_lote: int = Field(foreign_key="lote.id_lote")
    data_envio: datetime
    data_recebimento: Optional[datetime] = None
    status: str


# -------------------------
# FEEDBACK
# -------------------------
class Feedback(SQLModel, table=True):
    id_feedback: Optional[int] = Field(default=None, primary_key=True)
    id_paciente: int = Field(foreign_key="paciente.id_paciente")
    id_medicamento: int = Field(foreign_key="medicamento.id_medicamento")
    comentario: str
    tipo: str
    data: datetime


# -------------------------
# COMUNICAÇÃO
# -------------------------
class Mensagem(SQLModel, table=True):
    id_mensagem: Optional[int] = Field(default=None, primary_key=True)
    id_paciente: int = Field(foreign_key="user.id")
    id_farmaceutica: int = Field(foreign_key="user.id")
    id_medicamento: Optional[int] = Field(default=None, foreign_key="medicamento.id_medicamento")
    remetente_tipo: str  # 'paciente' ou 'farmaceutica'
    mensagem: str
    data_envio: datetime
    lida: bool = False


class ConteudoEducacional(SQLModel, table=True):
    id_conteudo: Optional[int] = Field(default=None, primary_key=True)
    id_medicamento: int = Field(foreign_key="medicamento.id_medicamento")
    titulo: str
    tipo: str  # 'doenca', 'medicamento', 'uso_correto', 'efeitos_colaterais'
    conteudo: str
    data_criacao: datetime