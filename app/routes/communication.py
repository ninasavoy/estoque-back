from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, Field, SQLModel
from typing import Optional, List
from datetime import datetime
from models import User, Medicamento
from database import get_session
from auth.dependencies import get_current_user, get_current_paciente, get_current_farmaceutica

router = APIRouter(prefix="/comunicacao", tags=["Canal de Comunicação"])


class ConteudoEducacional(SQLModel, table=True):
    id_conteudo: Optional[int] = Field(default=None, primary_key=True)
    id_medicamento: int = Field(foreign_key="medicamento.id_medicamento")
    titulo: str
    tipo: str  # 'doenca', 'medicamento', 'uso_correto', 'efeitos_colaterais'
    conteudo: str
    data_criacao: datetime


class MensagemCreate(SQLModel):
    id_farmaceutica: int
    id_medicamento: Optional[int] = None
    mensagem: str


class MensagemResponse(SQLModel):
    id_mensagem: int
    id_paciente: int
    id_farmaceutica: int
    id_medicamento: Optional[int]
    remetente_tipo: str
    mensagem: str
    data_envio: datetime
    lida: bool
    remetente_nome: str
    destinatario_nome: str


# ========================
# ROTAS PARA PACIENTES
# ========================

@router.post("/paciente/enviar-mensagem", response_model=Mensagem)
def paciente_enviar_mensagem(
    mensagem_data: MensagemCreate,
    current_user: User = Depends(get_current_paciente),
    session: Session = Depends(get_session)
):
    """Paciente envia mensagem para a farmacêutica"""
    # Verifica se a farmacêutica existe
    farmaceutica = session.get(User, mensagem_data.id_farmaceutica)
    if not farmaceutica or farmaceutica.tipo != "farmaceutica":
        raise HTTPException(status_code=404, detail="Farmacêutica não encontrada")
    
    mensagem = Mensagem(
        id_paciente=current_user.id,
        id_farmaceutica=mensagem_data.id_farmaceutica,
        id_medicamento=mensagem_data.id_medicamento,
        remetente_tipo="paciente",
        mensagem=mensagem_data.mensagem,
        data_envio=datetime.now(),
        lida=False
    )
    
    session.add(mensagem)
    session.commit()
    session.refresh(mensagem)
    return mensagem


@router.get("/paciente/minhas-conversas", response_model=List[MensagemResponse])
def paciente_listar_conversas(
    current_user: User = Depends(get_current_paciente),
    session: Session = Depends(get_session)
):
    """Lista todas as conversas do paciente"""
    mensagens = session.exec(
        select(Mensagem).where(
            Mensagem.id_paciente == current_user.id
        ).order_by(Mensagem.data_envio.desc())
    ).all()
    
    resultado = []
    for msg in mensagens:
        farmaceutica = session.get(User, msg.id_farmaceutica)
        resultado.append(MensagemResponse(
            id_mensagem=msg.id_mensagem,
            id_paciente=msg.id_paciente,
            id_farmaceutica=msg.id_farmaceutica,
            id_medicamento=msg.id_medicamento,
            remetente_tipo=msg.remetente_tipo,
            mensagem=msg.mensagem,
            data_envio=msg.data_envio,
            lida=msg.lida,
            remetente_nome=current_user.nome if msg.remetente_tipo == "paciente" else farmaceutica.nome,
            destinatario_nome=farmaceutica.nome if msg.remetente_tipo == "paciente" else current_user.nome
        ))
    
    return resultado


@router.get("/paciente/conteudo-educacional/{medicamento_id}")
def paciente_ver_conteudo(
    medicamento_id: int,
    current_user: User = Depends(get_current_paciente),
    session: Session = Depends(get_session)
):
    """Acessa conteúdo educacional sobre o medicamento"""
    conteudos = session.exec(
        select(ConteudoEducacional).where(
            ConteudoEducacional.id_medicamento == medicamento_id
        )
    ).all()
    
    medicamento = session.get(Medicamento, medicamento_id)
    
    return {
        "medicamento": {
            "id": medicamento.id_medicamento,
            "nome": medicamento.nome,
            "dosagem": medicamento.dosagem,
            "ingestao": medicamento.ingestao
        },
        "conteudos": [
            {
                "id": c.id_conteudo,
                "titulo": c.titulo,
                "tipo": c.tipo,
                "conteudo": c.conteudo,
                "data_criacao": c.data_criacao
            }
            for c in conteudos
        ]
    }


@router.patch("/paciente/marcar-lida/{mensagem_id}")
def paciente_marcar_lida(
    mensagem_id: int,
    current_user: User = Depends(get_current_paciente),
    session: Session = Depends(get_session)
):
    """Marca uma mensagem como lida"""
    mensagem = session.get(Mensagem, mensagem_id)
    
    if not mensagem or mensagem.id_paciente != current_user.id:
        raise HTTPException(status_code=404, detail="Mensagem não encontrada")
    
    mensagem.lida = True
    session.add(mensagem)
    session.commit()
    
    return {"message": "Mensagem marcada como lida"}


# ========================
# ROTAS PARA FARMACÊUTICAS
# ========================

@router.post("/farmaceutica/responder-mensagem", response_model=Mensagem)
def farmaceutica_responder(
    id_paciente: int,
    mensagem: str,
    id_medicamento: Optional[int] = None,
    current_user: User = Depends(get_current_farmaceutica),
    session: Session = Depends(get_session)
):
    """Farmacêutica responde mensagem do paciente"""
    # Verifica se o paciente existe
    paciente = session.get(User, id_paciente)
    if not paciente or paciente.tipo != "paciente":
        raise HTTPException(status_code=404, detail="Paciente não encontrado")
    
    nova_mensagem = Mensagem(
        id_paciente=id_paciente,
        id_farmaceutica=current_user.id,
        id_medicamento=id_medicamento,
        remetente_tipo="farmaceutica",
        mensagem=mensagem,
        data_envio=datetime.now(),
        lida=False
    )
    
    session.add(nova_mensagem)
    session.commit()
    session.refresh(nova_mensagem)
    return nova_mensagem


@router.get("/farmaceutica/mensagens-recebidas", response_model=List[MensagemResponse])
def farmaceutica_listar_mensagens(
    apenas_nao_lidas: bool = False,
    current_user: User = Depends(get_current_farmaceutica),
    session: Session = Depends(get_session)
):
    """Lista mensagens recebidas pela farmacêutica"""
    query = select(Mensagem).where(
        Mensagem.id_farmaceutica == current_user.id,
        Mensagem.remetente_tipo == "paciente"
    )
    
    if apenas_nao_lidas:
        query = query.where(Mensagem.lida == False)
    
    mensagens = session.exec(
        query.order_by(Mensagem.data_envio.desc())
    ).all()
    
    resultado = []
    for msg in mensagens:
        paciente = session.get(User, msg.id_paciente)
        resultado.append(MensagemResponse(
            id_mensagem=msg.id_mensagem,
            id_paciente=msg.id_paciente,
            id_farmaceutica=msg.id_farmaceutica,
            id_medicamento=msg.id_medicamento,
            remetente_tipo=msg.remetente_tipo,
            mensagem=msg.mensagem,
            data_envio=msg.data_envio,
            lida=msg.lida,
            remetente_nome=paciente.nome,
            destinatario_nome=current_user.nome
        ))
    
    return resultado


@router.get("/farmaceutica/conversas-por-paciente/{paciente_id}")
def farmaceutica_ver_conversa(
    paciente_id: int,
    current_user: User = Depends(get_current_farmaceutica),
    session: Session = Depends(get_session)
):
    """Visualiza toda a conversa com um paciente específico"""
    mensagens = session.exec(
        select(Mensagem).where(
            Mensagem.id_paciente == paciente_id,
            Mensagem.id_farmaceutica == current_user.id
        ).order_by(Mensagem.data_envio)
    ).all()
    
    paciente = session.get(User, paciente_id)
    
    return {
        "paciente": {
            "id": paciente.id,
            "nome": paciente.nome,
            "email": paciente.email
        },
        "mensagens": [
            {
                "id": m.id_mensagem,
                "remetente": m.remetente_tipo,
                "mensagem": m.mensagem,
                "data": m.data_envio,
                "lida": m.lida
            }
            for m in mensagens
        ]
    }


@router.post("/farmaceutica/criar-conteudo", response_model=ConteudoEducacional)
def farmaceutica_criar_conteudo(
    id_medicamento: int,
    titulo: str,
    tipo: str,
    conteudo: str,
    current_user: User = Depends(get_current_farmaceutica),
    session: Session = Depends(get_session)
):
    """Cria conteúdo educacional sobre medicamento/doença"""
    # Valida o tipo
    tipos_validos = ["doenca", "medicamento", "uso_correto", "efeitos_colaterais"]
    if tipo not in tipos_validos:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo inválido. Use: {', '.join(tipos_validos)}"
        )
    
    # Verifica se o medicamento existe
    medicamento = session.get(Medicamento, id_medicamento)
    if not medicamento:
        raise HTTPException(status_code=404, detail="Medicamento não encontrado")
    
    conteudo_obj = ConteudoEducacional(
        id_medicamento=id_medicamento,
        titulo=titulo,
        tipo=tipo,
        conteudo=conteudo,
        data_criacao=datetime.now()
    )
    
    session.add(conteudo_obj)
    session.commit()
    session.refresh(conteudo_obj)
    return conteudo_obj


@router.get("/farmaceutica/conteudos-criados")
def farmaceutica_listar_conteudos(
    current_user: User = Depends(get_current_farmaceutica),
    session: Session = Depends(get_session)
):
    """Lista todos os conteúdos educacionais criados"""
    conteudos = session.exec(select(ConteudoEducacional)).all()
    
    return [
        {
            "id": c.id_conteudo,
            "medicamento_id": c.id_medicamento,
            "titulo": c.titulo,
            "tipo": c.tipo,
            "data_criacao": c.data_criacao
        }
        for c in conteudos
    ]


@router.patch("/farmaceutica/marcar-lida/{mensagem_id}")
def farmaceutica_marcar_lida(
    mensagem_id: int,
    current_user: User = Depends(get_current_farmaceutica),
    session: Session = Depends(get_session)
):
    """Marca uma mensagem como lida"""
    mensagem = session.get(Mensagem, mensagem_id)
    
    if not mensagem or mensagem.id_farmaceutica != current_user.id:
        raise HTTPException(status_code=404, detail="Mensagem não encontrada")
    
    mensagem.lida = True
    session.add(mensagem)
    session.commit()
    
    return {"message": "Mensagem marcada como lida"}