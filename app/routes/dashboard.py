from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, func
from typing import List
from datetime import datetime, timedelta
from models import (
    SUS, UBS, ConteudoEducacional, Distribuidor, Farmaceutica, Medicamento, Lote, DistribuidorParaSUS, Paciente, SUSParaUBS, 
    UBSParaPaciente, Feedback, User
)
from database import get_session
from auth.dependencies import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboards"])

@router.get("/farmaceutica/overview")
def farmaceutica_dashboard(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Dashboard da Farmacêutica - Visibilidade completa da jornada do medicamento
    """
    # Verifica permissão
    if current_user.tipo not in ["admin", "farmaceutica"]:
        raise HTTPException(status_code=403, detail="Acesso restrito a farmacêuticas e administradores")
    
    # Se for farmacêutica, busca os dados dela
    if current_user.tipo == "farmaceutica":
        farmaceutica = session.exec(
            select(Farmaceutica).where(Farmaceutica.id_usuario == current_user.id)
        ).first()
        
        if not farmaceutica:
            raise HTTPException(status_code=404, detail="Farmacêutica não encontrada")
        
        # Filtra medicamentos da farmacêutica
        total_medicamentos = session.exec(
            select(func.count(Medicamento.id_medicamento))
            .where(Medicamento.id_farmaceutica == farmaceutica.id_farmaceutica)
        ).one()
        
        # Filtra lotes da farmacêutica
        total_lotes = session.exec(
            select(func.count(Lote.id_lote))
            .join(Medicamento)
            .where(Medicamento.id_farmaceutica == farmaceutica.id_farmaceutica)
        ).one()
        
        lotes_vencidos = session.exec(
            select(func.count(Lote.id_lote))
            .join(Medicamento)
            .where(
                Medicamento.id_farmaceutica == farmaceutica.id_farmaceutica,
                Lote.data_vencimento < datetime.now()
            )
        ).one()
        
        data_limite = datetime.now() + timedelta(days=30)
        lotes_proximos_vencimento = session.exec(
            select(func.count(Lote.id_lote))
            .join(Medicamento)
            .where(
                Medicamento.id_farmaceutica == farmaceutica.id_farmaceutica,
                Lote.data_vencimento.between(datetime.now(), data_limite)
            )
        ).one()
        
        # Rastreamento apenas dos lotes da farmacêutica
        em_distribuidor = session.exec(
            select(func.count(DistribuidorParaSUS.id_dps))
            .join(Lote)
            .join(Medicamento)
            .where(
                Medicamento.id_farmaceutica == farmaceutica.id_farmaceutica,
                DistribuidorParaSUS.status == "em transito"
            )
        ).one()
        
        em_sus = session.exec(
            select(func.count(SUSParaUBS.id_spu))
            .join(Lote)
            .join(Medicamento)
            .where(
                Medicamento.id_farmaceutica == farmaceutica.id_farmaceutica,
                SUSParaUBS.status == "em transito"
            )
        ).one()
        
        em_ubs = session.exec(
            select(func.count(UBSParaPaciente.id_upp))
            .join(Lote)
            .join(Medicamento)
            .where(
                Medicamento.id_farmaceutica == farmaceutica.id_farmaceutica,
                UBSParaPaciente.status == "em transito"
            )
        ).one()
        
        chegou_paciente = session.exec(
            select(func.count(UBSParaPaciente.id_upp))
            .join(Lote)
            .join(Medicamento)
            .where(
                Medicamento.id_farmaceutica == farmaceutica.id_farmaceutica,
                UBSParaPaciente.status == "recebido"
            )
        ).one()
        
        # Feedbacks apenas dos medicamentos da farmacêutica
        total_feedbacks = session.exec(
            select(func.count(Feedback.id_feedback))
            .join(Medicamento)
            .where(Medicamento.id_farmaceutica == farmaceutica.id_farmaceutica)
        ).one()
        
        # conteudo_educacional = session.exec(
        #     select(func.count(ConteudoEducacional.id_conteudo))
        #     .where(ConteudoEducacional.id_farmaceutica == farmaceutica.id_farmaceutica)
        # ).one()
    
    else:  # Admin vê tudo
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
                DistribuidorParaSUS.status == "em transito"
            )
        ).one()
        
        em_sus = session.exec(
            select(func.count(SUSParaUBS.id_spu)).where(
                SUSParaUBS.status == "em transito"
            )
        ).one()
        
        em_ubs = session.exec(
            select(func.count(UBSParaPaciente.id_upp)).where(
                UBSParaPaciente.status == "em transito"
            )
        ).one()
        
        chegou_paciente = session.exec(
            select(func.count(UBSParaPaciente.id_upp)).where(
                UBSParaPaciente.status == "recebido"
            )
        ).one()
        
        total_feedbacks = session.exec(
            select(func.count(Feedback.id_feedback))
        ).one()
        
        # conteudo_educacional = session.exec(
        #     select(func.count(ConteudoEducacional.id_conteudo))
        # ).one()

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
        }
        # "feedbacks_e_conteudos": {
        #     "total_feedbacks": total_feedbacks, 
        #     "conteudo_educacional": conteudo_educacional
        # }
    }


@router.get("/distribuidor/logistica")
def distribuidor_dashboard(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Dashboard do Distribuidor - Logística de entregas
    """
    # Verifica permissão
    if current_user.tipo not in ["admin", "distribuidor"]:
        raise HTTPException(status_code=403, detail="Acesso restrito a distribuidores e administradores")
    
    # Se for distribuidor, busca apenas seus dados
    if current_user.tipo == "distribuidor":
        distribuidor = session.exec(
            select(Distribuidor).where(Distribuidor.id_usuario == current_user.id)
        ).first()
        
        if not distribuidor:
            raise HTTPException(status_code=404, detail="Distribuidor não encontrado")
        
        pendentes = session.exec(
            select(DistribuidorParaSUS).where(
                DistribuidorParaSUS.id_distribuidor == distribuidor.id_distribuidor,
                DistribuidorParaSUS.status == "em transito"
            )
        ).all()
        
        concluidas = session.exec(
            select(DistribuidorParaSUS).where(
                DistribuidorParaSUS.id_distribuidor == distribuidor.id_distribuidor,
                DistribuidorParaSUS.status == "recebido"
            )
        ).all()
        
        # Total de entregas (histórico)
        total_entregas = session.exec(
            select(func.count(DistribuidorParaSUS.id_dps))
            .where(DistribuidorParaSUS.id_distribuidor == distribuidor.id_distribuidor)
        ).one()
        
    else:  # Admin vê tudo
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
        
        total_entregas = session.exec(
            select(func.count(DistribuidorParaSUS.id_dps))
        ).one()
    
    # Calcula tempo médio
    tempos_entrega = []
    for mov in concluidas:
        if mov.data_recebimento and mov.data_envio:
            delta = mov.data_recebimento - mov.data_envio
            tempos_entrega.append(delta.days)
    
    tempo_medio = sum(tempos_entrega) / len(tempos_entrega) if tempos_entrega else 0
    
    # Taxa de eficiência
    taxa_entrega = round((len(concluidas) / total_entregas * 100) if total_entregas > 0 else 0, 2)
    
    return {
        "entregas": {
            "pendentes": len(pendentes),
            "concluidas": len(concluidas),
            "total_historico": total_entregas,
            "tempo_medio_dias": round(tempo_medio, 1),
            "taxa_eficiencia": taxa_entrega
        },
        "pendentes_detalhes": [
            {
                "id": p.id_dps,
                "id_lote": p.id_lote,
                "id_sus": p.id_sus,
                "quantidade": p.quantidade,
                "data_envio": p.data_envio,
                "dias_em_transito": (datetime.now() - p.data_envio).days,
                "status": p.status
            }
            for p in pendentes[:10]
        ]
    }


@router.get("/sus/gerencial")
def sus_dashboard(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Dashboard do SUS - Gestão de estoque e distribuição
    """
    # Verifica permissão
    if current_user.tipo not in ["admin", "sus"]:
        raise HTTPException(status_code=403, detail="Acesso restrito ao SUS e administradores")
    
    # Se for SUS, busca apenas seus dados
    if current_user.tipo == "sus":
        sus = session.exec(
            select(SUS).where(SUS.id_usuario == current_user.id)
        ).first()
        
        if not sus:
            raise HTTPException(status_code=404, detail="SUS não encontrado")
        
        # Recebidos do distribuidor
        recebidos_distribuidor = session.exec(
            select(DistribuidorParaSUS).where(
                DistribuidorParaSUS.id_sus == sus.id_sus,
                DistribuidorParaSUS.status == "recebido"
            )
        ).all()
        
        # Aguardando recebimento
        aguardando_recebimento = session.exec(
            select(func.count(DistribuidorParaSUS.id_dps)).where(
                DistribuidorParaSUS.id_sus == sus.id_sus,
                DistribuidorParaSUS.status == "em transito"
            )
        ).one()
        
        # Enviados para UBS
        enviados_ubs = session.exec(
            select(SUSParaUBS).where(
                SUSParaUBS.id_sus == sus.id_sus
            )
        ).all()
        
        # UBS vinculadas
        total_ubs = session.exec(
            select(func.count(UBS.id_ubs)).where(
                UBS.id_sus == sus.id_sus
            )
        ).one()
        
        # Lotes com atenção (pegando os IDs dos lotes recebidos)
        lotes_ids = [r.id_lote for r in recebidos_distribuidor]
        data_limite = datetime.now() + timedelta(days=60)
        
        lotes_atencao = session.exec(
            select(Lote).where(
                Lote.id_lote.in_(lotes_ids),
                Lote.data_vencimento.between(datetime.now(), data_limite)
            )
        ).all() if lotes_ids else []
    
    else:  # Admin vê tudo
        recebidos_distribuidor = session.exec(
            select(DistribuidorParaSUS).where(
                DistribuidorParaSUS.status == "recebido"
            )
        ).all()
        
        aguardando_recebimento = session.exec(
            select(func.count(DistribuidorParaSUS.id_dps)).where(
                DistribuidorParaSUS.status == "em transito"
            )
        ).one()
        
        enviados_ubs = session.exec(
            select(SUSParaUBS)
        ).all()
        
        total_ubs = session.exec(
            select(func.count(UBS.id_ubs))
        ).one()
        
        data_limite = datetime.now() + timedelta(days=60)
        lotes_atencao = session.exec(
            select(Lote).where(
                Lote.data_vencimento.between(datetime.now(), data_limite)
            )
        ).all()
    
    em_estoque = len(recebidos_distribuidor) - len(enviados_ubs)
    taxa_distribuicao = round((len(enviados_ubs) / len(recebidos_distribuidor) * 100) if recebidos_distribuidor else 0, 2)
    
    return {
        "estoque": {
            "recebidos": len(recebidos_distribuidor),
            "aguardando_recebimento": aguardando_recebimento,
            "distribuidos_ubs": len(enviados_ubs),
            "em_estoque": max(0, em_estoque),
            "taxa_distribuicao": taxa_distribuicao
        },
        "rede": {
            "total_ubs_vinculadas": total_ubs
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
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Dashboard da UBS - Controle de estoque e distribuição aos pacientes
    """
    # Verifica permissão
    if current_user.tipo not in ["admin", "ubs"]:
        raise HTTPException(status_code=403, detail="Acesso restrito à UBS e administradores")
    
    # Se for UBS, busca apenas seus dados
    if current_user.tipo == "ubs":
        ubs = session.exec(
            select(UBS).where(UBS.id_usuario == current_user.id)
        ).first()
        
        if not ubs:
            raise HTTPException(status_code=404, detail="UBS não encontrada")
        
        # Recebidos do SUS
        recebidos = session.exec(
            select(SUSParaUBS).where(
                SUSParaUBS.id_ubs == ubs.id_ubs,
                SUSParaUBS.status == "recebido"
            )
        ).all()
        
        # Aguardando do SUS
        aguardando_sus = session.exec(
            select(func.count(SUSParaUBS.id_spu)).where(
                SUSParaUBS.id_ubs == ubs.id_ubs,
                SUSParaUBS.status == "em transito"
            )
        ).one()
        
        # Distribuídos aos pacientes
        distribuidos = session.exec(
            select(UBSParaPaciente).where(
                UBSParaPaciente.id_ubs == ubs.id_ubs
            )
        ).all()
        
        # Pacientes atendidos
        pacientes_atendidos = session.exec(
            select(func.count(func.distinct(UBSParaPaciente.id_paciente))).where(
                UBSParaPaciente.id_ubs == ubs.id_ubs
            )
        ).one()
        
        # Total de pacientes cadastrados
        total_pacientes = session.exec(
            select(func.count(Paciente.id_paciente)).where(
                Paciente.id_ubs == ubs.id_ubs
            )
        ).one()
        
    else:  # Admin vê tudo
        recebidos = session.exec(
            select(SUSParaUBS).where(
                SUSParaUBS.status == "recebido"
            )
        ).all()
        
        aguardando_sus = session.exec(
            select(func.count(SUSParaUBS.id_spu)).where(
                SUSParaUBS.status == "em transito"
            )
        ).one()
        
        distribuidos = session.exec(
            select(UBSParaPaciente)
        ).all()
        
        pacientes_atendidos = session.exec(
            select(func.count(func.distinct(UBSParaPaciente.id_paciente)))
        ).one()
        
        total_pacientes = session.exec(
            select(func.count(Paciente.id_paciente))
        ).one()
    
    em_estoque = len(recebidos) - len(distribuidos)
    taxa_atendimento = round((pacientes_atendidos / total_pacientes * 100) if total_pacientes > 0 else 0, 2)
    
    return {
        "estoque": {
            "total_recebido": len(recebidos),
            "aguardando_sus": aguardando_sus,
            "distribuido_pacientes": len(distribuidos),
            "em_estoque": max(0, em_estoque)
        },
        "pacientes": {
            "total_cadastrados": total_pacientes,
            "atendidos": pacientes_atendidos,
            "taxa_atendimento": taxa_atendimento
        },
        "distribuicoes_recentes": [
            {
                "id": d.id_upp,
                "id_paciente": d.id_paciente,
                "id_lote": d.id_lote,
                "data_envio": d.data_envio,
                "data_recebimento": d.data_recebimento,
                "status": d.status,
                "dias_para_entrega": (d.data_recebimento - d.data_envio).days if d.data_recebimento else None
            }
            for d in distribuidos[-10:]
        ]
    }


@router.get("/paciente/meus-medicamentos")
def paciente_dashboard(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Dashboard do Paciente - Acompanhamento de medicamentos e entregas
    """
    # Verifica permissão
    if current_user.tipo not in ["admin", "paciente"]:
        raise HTTPException(status_code=403, detail="Acesso restrito a pacientes e administradores")
    
    # Se for paciente, busca apenas seus dados
    if current_user.tipo == "paciente":
        paciente = session.exec(
            select(Paciente).where(Paciente.id_usuario == current_user.id)
        ).first()
        
        if not paciente:
            raise HTTPException(status_code=404, detail="Paciente não encontrado")
        
        # Medicamentos recebidos
        medicamentos_recebidos = session.exec(
            select(UBSParaPaciente).where(
                UBSParaPaciente.id_paciente == paciente.id_paciente,
                UBSParaPaciente.status == "recebido"
            )
        ).all()
        
        # Medicamentos em trânsito
        em_transito = session.exec(
            select(UBSParaPaciente).where(
                UBSParaPaciente.id_paciente == paciente.id_paciente,
                UBSParaPaciente.status == "em transito"
            )
        ).all()
        
        # Total de entregas históricas
        total_entregas = session.exec(
            select(func.count(UBSParaPaciente.id_upp)).where(
                UBSParaPaciente.id_paciente == paciente.id_paciente
            )
        ).one()
        
        # Feedbacks dados pelo paciente
        meus_feedbacks = session.exec(
            select(func.count(Feedback.id_feedback)).where(
                Feedback.id_paciente == paciente.id_paciente
            )
        ).one()
        
        # Detalhes dos medicamentos recebidos com informações do lote e medicamento
        detalhes_medicamentos = []
        for entrega in medicamentos_recebidos[-10:]:  # Últimos 10
            lote = session.exec(
                select(Lote).where(Lote.id_lote == entrega.id_lote)
            ).first()
            
            if lote:
                medicamento = session.exec(
                    select(Medicamento).where(Medicamento.id_medicamento == lote.id_medicamento)
                ).first()
                
                if medicamento:
                    detalhes_medicamentos.append({
                        "id_entrega": entrega.id_upp,
                        "medicamento": medicamento.nome,
                        "dosagem": medicamento.dosagem,
                        "ingestao": medicamento.ingestao,
                        "lote": lote.codigo_lote,
                        "data_recebimento": entrega.data_recebimento,
                        "data_vencimento": lote.data_vencimento,
                        "dias_ate_vencimento": (lote.data_vencimento - datetime.now()).days
                    })
        
        # Detalhes dos em trânsito
        detalhes_transito = []
        for entrega in em_transito:
            lote = session.exec(
                select(Lote).where(Lote.id_lote == entrega.id_lote)
            ).first()
            
            if lote:
                medicamento = session.exec(
                    select(Medicamento).where(Medicamento.id_medicamento == lote.id_medicamento)
                ).first()
                
                if medicamento:
                    detalhes_transito.append({
                        "id_entrega": entrega.id_upp,
                        "medicamento": medicamento.nome,
                        "dosagem": medicamento.dosagem,
                        "lote": lote.codigo_lote,
                        "data_envio": entrega.data_envio,
                        "dias_em_transito": (datetime.now() - entrega.data_envio).days
                    })
        
        # Informações da UBS
        ubs_info = session.exec(
            select(UBS).where(UBS.id_ubs == paciente.id_ubs)
        ).first()
        
    else:  # Admin não tem dashboard de paciente específico
        raise HTTPException(status_code=400, detail="Admin não possui dashboard de paciente")
    
    return {
        "resumo": {
            "total_medicamentos_recebidos": len(medicamentos_recebidos),
            "em_transito": len(em_transito),
            "total_entregas_historico": total_entregas,
            "feedbacks_dados": meus_feedbacks
        },
        "ubs_vinculada": {
            "nome": ubs_info.nome if ubs_info else None,
            "endereco": ubs_info.endereco if ubs_info else None,
            "contato": ubs_info.contato if ubs_info else None
        },
        "medicamentos_recebidos": detalhes_medicamentos,
        "aguardando_entrega": detalhes_transito
    }