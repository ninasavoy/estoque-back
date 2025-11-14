from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List
from datetime import datetime
from models import (
    DistribuidorParaSUS,
    Paciente,
    SUSParaUBS,
    UBSParaPaciente,
    Distribuidor,
    SUS,
    UBS,
    User,
)
from database import get_session
from auth.dependencies import get_current_user

# Routers separados
router_dps = APIRouter(prefix="/distribuidores-sus", tags=["Distribuidor → SUS"])
router_spu = APIRouter(prefix="/sus-ubs", tags=["SUS → UBS"])
router_upp = APIRouter(prefix="/ubs-pacientes", tags=["UBS → Paciente"])

# ==========================================================
# DISTRIBUIDOR → SUS
# ==========================================================

@router_dps.post("/", response_model=DistribuidorParaSUS, status_code=status.HTTP_201_CREATED)
def create_dps(
    dps: DistribuidorParaSUS,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    if current_user.tipo not in ["admin", "distribuidor"]:
        raise HTTPException(status_code=403, detail="Acesso restrito a distribuidores e administradores")

    if current_user.tipo == "distribuidor":
        distribuidor = session.exec(
            select(Distribuidor).where(Distribuidor.id_usuario == current_user.id)
        ).first()
        if not distribuidor:
            raise HTTPException(status_code=404, detail="Distribuidor não encontrado")
        dps.id_distribuidor = distribuidor.id_distribuidor

    dps.data_envio = datetime.now()
    dps.status = "em transito"

    session.add(dps)
    session.commit()
    session.refresh(dps)
    return dps


@router_dps.get("/", response_model=List[DistribuidorParaSUS])
def list_dps(session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):

    query = select(DistribuidorParaSUS)

    # DISTRIBUIDOR só vê as dele
    if current_user.tipo == "distribuidor":
        distribuidor = session.exec(
            select(Distribuidor).where(Distribuidor.id_usuario == current_user.id)
        ).first()

        if not distribuidor:
            raise HTTPException(404, "Distribuidor não encontrado")

        query = query.where(DistribuidorParaSUS.id_distribuidor == distribuidor.id_distribuidor)

    # SUS só vê movimentações destinadas a ele
    if current_user.tipo == "sus":
        sus = session.exec(select(SUS).where(SUS.id_usuario == current_user.id)).first()
    
        if not sus:
            raise HTTPException(404, "SUS não encontrado")
        query = query.where(DistribuidorParaSUS.id_sus == sus.id_sus)

    if current_user.tipo not in ["admin", "distribuidor", "sus"]:
        raise HTTPException(403, "Sem permissão para visualizar")

    return session.exec(query).all()



@router_dps.get("/{id_dps}", response_model=DistribuidorParaSUS)
def get_dps(id_dps: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    dps = session.get(DistribuidorParaSUS, id_dps)
    if not dps:
        raise HTTPException(404, "Movimentação não encontrada")

    if current_user.tipo == "admin":
        return dps

    if current_user.tipo == "distribuidor":
        distribuidor = session.exec(
            select(Distribuidor).where(Distribuidor.id_usuario == current_user.id)
        ).first()
    
        if not distribuidor:
            raise HTTPException(404, "Distribuidor não encontrado")
        if dps.id_distribuidor != distribuidor.id_distribuidor:
            raise HTTPException(403, "Sem permissão")
        return dps

    if current_user.tipo == "sus":
        sus = session.exec(select(SUS).where(SUS.id_usuario == current_user.id)).first()
    
        if not sus:
            raise HTTPException(404, "SUS não encontrado")
        if dps.id_sus != sus.id_sus:
            raise HTTPException(403, "Sem permissão")
        return dps

    raise HTTPException(403, "Sem permissão")


@router_dps.put("/{id_dps}", response_model=DistribuidorParaSUS)
def update_dps(id_dps: int, dps_data: DistribuidorParaSUS, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):

    dps = session.get(DistribuidorParaSUS, id_dps)
    if not dps:
        raise HTTPException(404, "Movimentação não encontrada")

    if current_user.tipo not in ["admin", "distribuidor"]:
        raise HTTPException(403, "Sem permissão")

    if current_user.tipo == "distribuidor":
        distribuidor = session.exec(
            select(Distribuidor).where(Distribuidor.id_usuario == current_user.id)
        ).first()
    
        if not distribuidor:
            raise HTTPException(404, "Distribuidor não encontrado")
        if dps.id_distribuidor != distribuidor.id_distribuidor:
            raise HTTPException(403, "Você só pode alterar suas próprias movimentações")

    # aplica atualização
    for k, v in dps_data.model_dump(exclude_unset=True, exclude={"id_dps"}).items():
        setattr(dps, k, v)

    session.add(dps)
    session.commit()
    session.refresh(dps)
    return dps


@router_dps.delete("/{id_dps}", status_code=204)
def delete_dps(id_dps: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    dps = session.get(DistribuidorParaSUS, id_dps)
    if not dps:
        raise HTTPException(404, "Movimentação não encontrada")

    if current_user.tipo not in ["admin", "distribuidor"]:
        raise HTTPException(403, "Sem permissão")

    if current_user.tipo == "distribuidor":
        distribuidor = session.exec(
            select(Distribuidor).where(Distribuidor.id_usuario == current_user.id)
        ).first()
    
        if not distribuidor:
            raise HTTPException(404, "Distribuidor não encontrado")
        if dps.id_distribuidor != distribuidor.id_distribuidor:
            raise HTTPException(403, "Você só pode excluir suas próprias movimentações")

    session.delete(dps)
    session.commit()


@router_dps.post("/{id_dps}/confirmar")
def confirmar_recebimento_dps(
    id_dps: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    if current_user.tipo != "sus" and current_user.tipo != "admin":
        raise HTTPException(status_code=403, detail="Acesso restrito a SUS")
    
    # ✅ MOVER A VERIFICAÇÃO PARA DEPOIS (admin não precisa de SUS)
    dps = session.get(DistribuidorParaSUS, id_dps)
    if not dps:
        raise HTTPException(status_code=404, detail="Movimentação não encontrada")
    
    # ✅ SÓ BUSCA SUS SE NÃO FOR ADMIN
    if current_user.tipo == "sus":
        sus = session.exec(select(SUS).where(SUS.id_usuario == current_user.id)).first()
        if not sus:
            raise HTTPException(status_code=404, detail="SUS não encontrado")
        if dps.id_sus != sus.id_sus:
            raise HTTPException(status_code=403, detail="Você não é o destinatário desta movimentação")

    dps.status = "recebido"
    dps.data_recebimento = datetime.now()

    session.add(dps)
    session.commit()
    return {"message": "Recebimento confirmado com sucesso"}


# ==========================================================
# SUS → UBS
# ==========================================================

@router_spu.post("/", response_model=SUSParaUBS, status_code=status.HTTP_201_CREATED)
def create_spu(
    spu: SUSParaUBS,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    if current_user.tipo not in ["admin", "sus"]:
        raise HTTPException(status_code=403, detail="Acesso restrito a SUS e administradores")

    if current_user.tipo == "sus":
        sus = session.exec(select(SUS).where(SUS.id_usuario == current_user.id)).first()
        if not sus:
            raise HTTPException(status_code=404, detail="SUS não encontrado")
        spu.id_sus = sus.id_sus

    spu.data_envio = datetime.now()
    spu.status = "em transito"

    session.add(spu)
    session.commit()
    session.refresh(spu)
    return spu


@router_spu.get("/", response_model=List[SUSParaUBS])
def list_spu(session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):

    query = select(SUSParaUBS)

    if current_user.tipo == "sus":
        sus = session.exec(select(SUS).where(SUS.id_usuario == current_user.id)).first()
    
        if not sus:
            raise HTTPException(404, "SUS não encontrado")
        query = query.where(SUSParaUBS.id_sus == sus.id_sus)

    if current_user.tipo == "ubs":
        ubs = session.exec(select(UBS).where(UBS.id_usuario == current_user.id)).first()
    
        if not ubs:
            raise HTTPException(404, "UBS não encontrada")
        query = query.where(SUSParaUBS.id_ubs == ubs.id_ubs)

    if current_user.tipo not in ["admin", "sus", "ubs"]:
        raise HTTPException(403, "Sem permissão")

    return session.exec(query).all()


@router_spu.get("/{id_spu}", response_model=SUSParaUBS)
def get_spu(
    id_spu: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    spu = session.get(SUSParaUBS, id_spu)
    if not spu:
        raise HTTPException(404, "Movimentação não encontrada")

    # ADMIN pode tudo
    if current_user.tipo == "admin":
        return spu

    # SUS só vê movimentações enviadas por ele
    if current_user.tipo == "sus":
        sus = session.exec(select(SUS).where(SUS.id_usuario == current_user.id)).first()
    
        if not sus:
            raise HTTPException(404, "SUS não encontrado")
        if spu.id_sus != sus.id_sus:
            raise HTTPException(403, "Sem permissão para visualizar esta movimentação")
        return spu

    # UBS só vê movimentação destinada a ela
    if current_user.tipo == "ubs":
        ubs = session.exec(select(UBS).where(UBS.id_usuario == current_user.id)).first()
    
        if not ubs:
            raise HTTPException(404, "UBS não encontrada")
        if spu.id_ubs != ubs.id_ubs:
            raise HTTPException(403, "Sem permissão para visualizar esta movimentação")
        return spu

    raise HTTPException(403, "Sem permissão")


@router_spu.put("/{id_spu}", response_model=SUSParaUBS)
def update_spu(
    id_spu: int,
    spu_data: SUSParaUBS,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    spu = session.get(SUSParaUBS, id_spu)
    if not spu:
        raise HTTPException(404, "Movimentação não encontrada")

    # Apenas admin e SUS podem atualizar
    if current_user.tipo not in ["admin", "sus"]:
        raise HTTPException(403, "Sem permissão")

    # SUS só pode alterar suas próprias movimentações
    if current_user.tipo == "sus":
        sus = session.exec(select(SUS).where(SUS.id_usuario == current_user.id)).first()
    
        if not sus:
            raise HTTPException(404, "SUS não encontrado")
        if spu.id_sus != sus.id_sus:
            raise HTTPException(403, "Você só pode alterar movimentações enviadas pelo seu SUS")

    for k, v in spu_data.model_dump(exclude_unset=True, exclude={"id_spu"}).items():
        setattr(spu, k, v)

    session.add(spu)
    session.commit()
    session.refresh(spu)
    return spu


@router_spu.delete("/{id_spu}", status_code=204)
def delete_spu(
    id_spu: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    spu = session.get(SUSParaUBS, id_spu)
    if not spu:
        raise HTTPException(404, "Movimentação não encontrada")

    # Apenas admin e SUS podem deletar
    if current_user.tipo not in ["admin", "sus"]:
        raise HTTPException(403, "Sem permissão")

    # SUS só pode excluir as suas
    if current_user.tipo == "sus":
        sus = session.exec(select(SUS).where(SUS.id_usuario == current_user.id)).first()
    
        if not sus:
            raise HTTPException(404, "SUS não encontrado")
        if spu.id_sus != sus.id_sus:
            raise HTTPException(403, "Você só pode excluir suas próprias movimentações")

    session.delete(spu)
    session.commit()


@router_spu.post("/{id_spu}/confirmar")
def confirmar_recebimento_spu(
    id_spu: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    if current_user.tipo != "ubs" and current_user.tipo != "admin":
        raise HTTPException(status_code=403, detail="Acesso restrito a UBS")
    
    # ✅ BUSCAR MOVIMENTAÇÃO PRIMEIRO
    spu = session.get(SUSParaUBS, id_spu)
    if not spu:
        raise HTTPException(status_code=404, detail="Movimentação não encontrada")
    
    # ✅ SÓ BUSCA UBS SE NÃO FOR ADMIN
    if current_user.tipo == "ubs":
        ubs = session.exec(select(UBS).where(UBS.id_usuario == current_user.id)).first()
        if not ubs:
            raise HTTPException(status_code=404, detail="UBS não encontrada")
        if spu.id_ubs != ubs.id_ubs:
            raise HTTPException(status_code=403, detail="Você não é o destinatário desta movimentação")

    spu.status = "recebido"
    spu.data_recebimento = datetime.now()

    session.add(spu)
    session.commit()
    return {"message": "Recebimento confirmado com sucesso"}


# ==========================================================
# UBS → PACIENTE
# ==========================================================

@router_upp.post("/", response_model=UBSParaPaciente, status_code=status.HTTP_201_CREATED)
def create_upp(
    upp: UBSParaPaciente,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    if current_user.tipo not in ["admin", "ubs"]:
        raise HTTPException(status_code=403, detail="Acesso restrito a UBS e administradores")

    if current_user.tipo == "ubs":
        ubs = session.exec(select(UBS).where(UBS.id_usuario == current_user.id)).first()
        if not ubs:
            raise HTTPException(status_code=404, detail="UBS não encontrada")
        upp.id_ubs = ubs.id_ubs

    upp.data_envio = datetime.now()
    upp.status = "em transito"

    session.add(upp)
    session.commit()
    session.refresh(upp)
    return upp


@router_upp.get("/", response_model=List[UBSParaPaciente])
def list_upp(session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):

    query = select(UBSParaPaciente)

    if current_user.tipo == "ubs":
        ubs = session.exec(select(UBS).where(UBS.id_usuario == current_user.id)).first()
    
        if not ubs:
            raise HTTPException(404, "UBS não encontrada")
        query = query.where(UBSParaPaciente.id_ubs == ubs.id_ubs)

    if current_user.tipo == "paciente":
        paciente = session.exec(select(Paciente).where(Paciente.id_usuario == current_user.id)).first()
    
        if not paciente:
            raise HTTPException(404, "Paciente não encontrado")
        query = query.where(UBSParaPaciente.id_paciente == paciente.id_paciente)

    if current_user.tipo not in ["admin", "ubs", "paciente"]:
        raise HTTPException(403, "Sem permissão")

    return session.exec(query).all()


@router_upp.get("/{id_upp}", response_model=UBSParaPaciente)
def get_upp(
    id_upp: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    upp = session.get(UBSParaPaciente, id_upp)
    if not upp:
        raise HTTPException(404, "Movimentação não encontrada")

    if current_user.tipo == "admin":
        return upp

    if current_user.tipo == "ubs":
        ubs = session.exec(select(UBS).where(UBS.id_usuario == current_user.id)).first()
    
        if not ubs:
            raise HTTPException(404, "UBS não encontrada")
        if upp.id_ubs != ubs.id_ubs:
            raise HTTPException(403, "Sem permissão")
        return upp

    if current_user.tipo == "paciente":
        paciente = session.exec(select(Paciente).where(Paciente.id_usuario == current_user.id)).first()
    
        if not paciente:
            raise HTTPException(404, "Paciente não encontrado")
        if upp.id_paciente != paciente.id_paciente:
            raise HTTPException(403, "Sem permissão")
        return upp

    raise HTTPException(403, "Sem permissão")


@router_upp.put("/{id_upp}", response_model=UBSParaPaciente)
def update_upp(
    id_upp: int,
    upp_data: UBSParaPaciente,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    upp = session.get(UBSParaPaciente, id_upp)
    if not upp:
        raise HTTPException(404, "Movimentação não encontrada")

    if current_user.tipo not in ["admin", "ubs"]:
        raise HTTPException(403, "Sem permissão")

    if current_user.tipo == "ubs":
        ubs = session.exec(select(UBS).where(UBS.id_usuario == current_user.id)).first()
    
        if not ubs:
            raise HTTPException(404, "UBS não encontrada")
        if upp.id_ubs != ubs.id_ubs:
            raise HTTPException(403, "Você só pode alterar movimentações da sua UBS")

    for k, v in upp_data.model_dump(exclude_unset=True, exclude={"id_upp"}).items():
        setattr(upp, k, v)

    session.add(upp)
    session.commit()
    session.refresh(upp)
    return upp


@router_upp.delete("/{id_upp}", status_code=204)
def delete_upp(
    id_upp: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    upp = session.get(UBSParaPaciente, id_upp)
    if not upp:
        raise HTTPException(404, "Movimentação não encontrada")

    if current_user.tipo not in ["admin", "ubs"]:
        raise HTTPException(403, "Sem permissão")

    if current_user.tipo == "ubs":
        ubs = session.exec(select(UBS).where(UBS.id_usuario == current_user.id)).first()
    
        if not ubs:
            raise HTTPException(404, "UBS não encontrada")
        if upp.id_ubs != ubs.id_ubs:
            raise HTTPException(403, "Você só pode excluir movimentações da sua UBS")

    session.delete(upp)
    session.commit()


@router_upp.post("/{id_upp}/confirmar")
def confirmar_recebimento_upp(
    id_upp: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    if current_user.tipo != "paciente" and current_user.tipo != "admin":
        raise HTTPException(status_code=403, detail="Acesso restrito a pacientes")
    
    # ✅ BUSCAR MOVIMENTAÇÃO PRIMEIRO
    upp = session.get(UBSParaPaciente, id_upp)
    if not upp:
        raise HTTPException(status_code=404, detail="Movimentação não encontrada")
    
    # ✅ SÓ BUSCA PACIENTE SE NÃO FOR ADMIN
    if current_user.tipo == "paciente":
        paciente = session.exec(
            select(Paciente).where(Paciente.id_usuario == current_user.id)
        ).first()

        if not paciente:
            raise HTTPException(status_code=404, detail="Paciente não encontrado")
        
        if upp.id_paciente != paciente.id_paciente:
            raise HTTPException(status_code=403, detail="Você não é o destinatário desta movimentação")

    upp.status = "recebido"
    upp.data_recebimento = datetime.now()

    session.add(upp)
    session.commit()
    return {"message": "Recebimento confirmado com sucesso"}