from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, func
from typing import List
from datetime import datetime, timedelta
from models import (
    Medicamento, Lote, DistribuidorParaSUS, SUSParaUBS, 
    UBSParaPaciente, Feedback, User
)
from database import get_session
from auth.dependencies import (
    get_current_farmaceutica, get_current_distribuidor,
    get_current_sus, get_current_ubs
)

router = APIRouter(prefix="/dashboard", tags=["Dashboards"])


@router.get("/farmaceutica/overview")
def farmaceutica_dashboard(
    current_user: User = Depends(get_current_farmaceutica),
    session: Session = Depends(get_session)
):
    """
    Dashboard da Farmacêutica - Visibilidade completa da jornada do medicamento
    - Onde os medicamentos estão
    - Se chegaram ao paciente final
    - Validade, tempo médio de distribuição
    """
    # Total de medicamentos cadastrados
    total_medicamentos = session.exec(
        select(func.count(Medicamento.id_medicamento))
    ).one()
    
    # Total de lotes
    total_lotes = session.exec(
        select(func.count(Lote.id_lote))
    ).one()
    
    # Lotes vencidos
    lotes_vencidos = session.exec(
        select(func.count(Lote.id_lote)).where(
            Lote.data_vencimento < datetime.now()
        )
    ).one()
    
    # Lotes próximos do vencimento (30 dias)
    data_limite = datetime.now() + timedelta(days=30)
    lotes_proximos_vencimento = session.exec(
        select(func.count(Lote.id_lote)).where(
            Lote.data_vencimento.between(datetime.now(), data_limite)
        )
    ).one()
    
    # Medicamentos por estágio da cadeia
    em_distribuidor = session.exec(
        select(func.count(DistribuidorParaSUS.id_dps)).where(
            DistribuidorParaSUS.status == "em_transito"
        )
    ).one()
    
    em_sus = session.exec(
        select(func.count(SUSParaUBS.id_spu)).where(
            SUSParaUBS.status == "em_transito"
        )
    ).one()
    
    em_ubs = session.exec(
        select(func.count(UBSParaPaciente.id_upp)).where(
            UBSParaPaciente.status == "em_transito"
        )
    ).one()
    
    chegou_paciente = session.exec(
        select(func.count(UBSParaPaciente.id_upp)).where(
            UBSParaPaciente.status == "entregue"
        )
    ).one()
    
    # Feedbacks recebidos
    total_feedbacks = session.exec(
        select(func.count(Feedback.id_feedback))
    ).one()
    
    return {
        "medicamentos": {
            "total": total_medicamentos,
            "lotes_total": total_lotes,
            "lotes_vencidos": lotes_vencidos,
            "lotes_proximos_vencimento": lotes_proximos_vencimento
        },
        "rastreamento": {
            "em_distribuidor": em_distribuidor,
            "em_sus": em_sus,
            "em_ubs": em_ubs,
            "chegou_paciente": chegou_paciente,
            "taxa_entrega": round((chegou_paciente / total_lotes * 100) if total_lotes > 0 else 0, 2)
        },
        "feedbacks": {
            "total": total_feedbacks
        }
    }


@router.get("/distribuidor/logistica")
def distribuidor_dashboard(
    current_user: User = Depends(get_current_distribuidor),
    session: Session = Depends(get_session)
):
    """
    Dashboard do Distribuidor - Informações logísticas
    - Entregas pendentes
    - Entregas concluídas
    - Tempo médio de entrega
    """
    # Assumindo que existe relação entre User e Distribuidor
    # Por simplificação, vamos buscar todas as movimentações
    
    pendentes = session.exec(
        select(DistribuidorParaSUS).where(
            DistribuidorParaSUS.status == "em_transito"
        )
    ).all()
    
    concluidas = session.exec(
        select(DistribuidorParaSUS).where(
            DistribuidorParaSUS.status == "entregue"
        )
    ).all()
    
    # Calcula tempo médio de entrega
    tempos_entrega = []
    for mov in concluidas:
        if mov.data_recebimento and mov.data_envio:
            delta = mov.data_recebimento - mov.data_envio
            tempos_entrega.append(delta.days)
    
    tempo_medio = sum(tempos_entrega) / len(tempos_entrega) if tempos_entrega else 0
    
    return {
        "entregas": {
            "pendentes": len(pendentes),
            "concluidas": len(concluidas),
            "tempo_medio_dias": round(tempo_medio, 1)
        },
        "pendentes_detalhes": [
            {
                "id": p.id_dps,
                "id_lote": p.id_lote,
                "data_envio": p.data_envio,
                "status": p.status
            }
            for p in pendentes[:10]  # Últimas 10
        ]
    }


@router.get("/sus/gerencial")
def sus_dashboard(
    current_user: User = Depends(get_current_sus),
    session: Session = Depends(get_session)
):
    """
    Dashboard do SUS - Informações gerenciais
    - Onde os medicamentos estão
    - Tempo de validade
    - Necessidades de remanejamento
    """
    # Medicamentos em estoque no SUS (recebidos mas não enviados)
    recebidos_distribuidor = session.exec(
        select(DistribuidorParaSUS).where(
            DistribuidorParaSUS.status == "entregue"
        )
    ).all()
    
    enviados_ubs = session.exec(
        select(SUSParaUBS)
    ).all()
    
    # Lotes que precisam de atenção (vencimento próximo)
    data_limite = datetime.now() + timedelta(days=60)
    lotes_atencao = session.exec(
        select(Lote).where(
            Lote.data_vencimento.between(datetime.now(), data_limite)
        )
    ).all()
    
    return {
        "estoque": {
            "recebidos": len(recebidos_distribuidor),
            "distribuidos_ubs": len(enviados_ubs),
            "em_estoque": len(recebidos_distribuidor) - len(enviados_ubs)
        },
        "alertas": {
            "lotes_vencimento_proximo": len(lotes_atencao),
            "necessita_remanejamento": len([l for l in lotes_atencao if l.quantidade > 100])
        },
        "lotes_atencao": [
            {
                "id_lote": l.id_lote,
                "codigo": l.codigo_lote,
                "quantidade": l.quantidade,
                "vencimento": l.data_vencimento,
                "dias_restantes": (l.data_vencimento - datetime.now()).days
            }
            for l in lotes_atencao[:10]
        ]
    }


@router.get("/ubs/estoque")
def ubs_dashboard(
    current_user: User = Depends(get_current_ubs),
    session: Session = Depends(get_session)
):
    """
    Dashboard da UBS - Controle de estoque local
    - Medicamentos em estoque
    - Distribuídos para pacientes
    - Alertas de estoque baixo
    """
    # Medicamentos recebidos pela UBS
    recebidos = session.exec(
        select(SUSParaUBS).where(
            SUSParaUBS.status == "entregue"
        )
    ).all()
    
    # Medicamentos distribuídos para pacientes
    distribuidos = session.exec(
        select(UBSParaPaciente)
    ).all()
    
    return {
        "estoque": {
            "total_recebido": len(recebidos),
            "distribuido_pacientes": len(distribuidos),
            "em_estoque": len(recebidos) - len(distribuidos)
        },
        "distribuicoes_recentes": [
            {
                "id": d.id_upp,
                "id_paciente": d.id_paciente,
                "id_lote": d.id_lote,
                "data_envio": d.data_envio,
                "status": d.status
            }
            for d in distribuidos[-10:]  # Últimas 10
        ]
    }