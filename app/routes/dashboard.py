from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, func
from typing import List
from datetime import datetime, timedelta
from models import (
    ConteudoEducacional, Medicamento, Lote, DistribuidorParaSUS, SUSParaUBS, 
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
    total_medicamentos = session.exec(
        select(func.count(Medicamento.id_medicamento))
    ).one()
    
    total_lotes = session.exec(
        select(func.count(Lote.id_lote))
    ).one()
    
    lotes_vencidos = session.exec(
        select(func.count(Lote.id_lote)).where(
            Lote.data_vencimento < datetime.now()
        )
    ).one()
    
    data_limite = datetime.now() + timedelta(days=30)
    lotes_proximos_vencimento = session.exec(
        select(func.count(Lote.id_lote)).where(
            Lote.data_vencimento.between(datetime.now(), data_limite)
        )
    ).one()
    
    
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
    
    total_feedbacks = session.exec(
        select(func.count(Feedback.id_feedback))
    ).one()
    
    conteudo_educacional = session.exec(
        select(func.count(ConteudoEducacional.id_feedback))
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
        "feedbacks e conteúdos": {
            "total": total_feedbacks, 
            "conteudo_educacional": conteudo_educacional
        }
    }


@router.get("/distribuidor/logistica")
def distribuidor_dashboard(
    current_user: User = Depends(get_current_distribuidor),
    session: Session = Depends(get_session)
):

    pendentes = session.exec(
        select(DistribuidorParaSUS).where(
            DistribuidorParaSUS.status == "em transito"
        )
    ).all()
    
    concluidas = session.exec(
        select(DistribuidorParaSUS).where(
            DistribuidorParaSUS.status == "recebido"
        )
    ).all()
    
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
    # Medicamentos em estoque no SUS (recebidos mas não enviados)
    recebidos_distribuidor = session.exec(
        select(DistribuidorParaSUS).where(
            DistribuidorParaSUS.status == "recebido"
        )
    ).all()
    
    enviados_ubs = session.exec(
        select(SUSParaUBS)
    ).all()
    
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