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
    tipo: str  # 'farmaceutica', 'distribuidor', 'sus', 'ubs', 'paciente', 'admin'


class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    ativo: bool = Field(default=False)


# -------------------------
# ADMINISTRADOR
# -------------------------

class Administrador(SQLModel, table=True):
    id_administrador: Optional[int] = Field(default=None, primary_key=True)
    nome: str
    email: str
    contato: str
    id_usuario: int = Field(foreign_key="user.id")


# -------------------------
# FARMACÊUTICA / MEDICAMENTOS / LOTES
# -------------------------
class Farmaceutica(SQLModel, table=True):
    id_farmaceutica: Optional[int] = Field(default=None, primary_key=True)
    nome: str
    cnpj: str
    contato: str
    id_usuario: int = Field(foreign_key="user.id")

    medicamentos: List["Medicamento"] = Relationship(back_populates="farmaceutica")


class FarmaceuticaCreate(SQLModel):
    nome: str
    cnpj: str
    contato: str


class Medicamento(SQLModel, table=True):
    id_medicamento: Optional[int] = Field(default=None, primary_key=True)
    nome: str
    ingestao: Optional[str] = None
    dosagem: Optional[str] = None
    preco: float
    alto_custo: bool
    id_farmaceutica: int = Field(foreign_key="farmaceutica.id_farmaceutica")

    farmaceutica: Optional[Farmaceutica] = Relationship(back_populates="medicamentos")
    lotes: List["Lote"] = Relationship(back_populates="medicamento")


class Lote(SQLModel, table=True):
    id_lote: Optional[int] = Field(default=None, primary_key=True)
    codigo_lote: str
    data_fabricacao: datetime
    data_vencimento: datetime
    quantidade: int
    id_medicamento: int = Field(foreign_key="medicamento.id_medicamento")

    medicamento: Optional[Medicamento] = Relationship(back_populates="lotes")


# -------------------------
# DISTRIBUIDOR
# -------------------------
class Distribuidor(SQLModel, table=True):
    id_distribuidor: Optional[int] = Field(default=None, primary_key=True)
    nome: str
    localizacao: str
    contato: str
    id_usuario: int = Field(foreign_key="user.id")

class DistribuidorCreate(SQLModel):
    nome: str
    localizacao: str
    contato: str

# -------------------------
# SUS
# -------------------------
class SUS(SQLModel, table=True):
    id_sus: Optional[int] = Field(default=None, primary_key=True)
    regiao: str
    contato_gestor: str
    nome_gestor: str
    id_usuario: int = Field(foreign_key="user.id")

    ubs: List["UBS"] = Relationship(back_populates="sus")

class SUSCreate(SQLModel):
    regiao: str
    contato_gestor: str
    nome_gestor: str

# -------------------------
# UBS
# -------------------------
class UBS(SQLModel, table=True):
    id_ubs: Optional[int] = Field(default=None, primary_key=True)
    nome: str
    contato: str
    endereco: str
    id_sus: int = Field(foreign_key="sus.id_sus")
    id_usuario: int = Field(foreign_key="user.id")

    sus: Optional[SUS] = Relationship(back_populates="ubs")
    pacientes: List["Paciente"] = Relationship(back_populates="ubs")

class UBSCreate(SQLModel):
    nome: str
    contato: str
    endereco: str
    id_sus: Optional[int] = Field(default=None, foreign_key="sus.id_sus")

# -------------------------
# PACIENTE
# -------------------------
class Paciente(SQLModel, table=True):
    id_paciente: Optional[int] = Field(default=None, primary_key=True)
    nome: str
    sobrenome: str
    cpf: str
    contato: str
    id_ubs: int = Field(foreign_key="ubs.id_ubs")
    id_usuario: int = Field(foreign_key="user.id")

    ubs: Optional[UBS] = Relationship(back_populates="pacientes")

class PacienteCreate(SQLModel):
    nome: str
    sobrenome: str
    cpf: str
    contato: str
    id_ubs: int = Field(foreign_key="ubs.id_ubs")

# -------------------------
# MOVIMENTAÇÕES
# -------------------------
class DistribuidorParaSUS(SQLModel, table=True):
    id_dps: Optional[int] = Field(default=None, primary_key=True)
    id_distribuidor: int = Field(foreign_key="distribuidor.id_distribuidor")
    id_sus: int = Field(foreign_key="sus.id_sus")
    id_lote: int = Field(foreign_key="lote.id_lote")
    quantidade: int
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
# CONTEÚDO EDUCACIONAL
# -------------------------

class ConteudoEducacional(SQLModel, table=True):
    id_conteudo: Optional[int] = Field(default=None, primary_key=True)
    id_medicamento: int = Field(foreign_key="medicamento.id_medicamento")
    titulo: str
    tipo: str  # 'doenca', 'medicamento', 'uso_correto', 'efeitos_colaterais'
    conteudo: str
    data_criacao: datetime
