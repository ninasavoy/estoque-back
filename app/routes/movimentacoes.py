from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from datetime import datetime
from typing import List, Optional

from database import get_session
from models import DistribuidorParaSUS, SUSParaUBS, UBSParaPaciente

router = APIRouter(prefix="/movimentacoes", tags=["Movimentações"])

# ==========================================================
#  DISTRIBUIDOR → SUS
# ==========================================================

@router.get("/distribuidor-sus", response_model=List[DistribuidorParaSUS])
def listar_mov_dps(session: Session = Depends(get_session)):
    """Lista todas as movimentações Distribuidor → SUS"""
    return session.exec(select(DistribuidorParaSUS)).all()


@router.get("/distribuidor-sus/{id_dps}", response_model=DistribuidorParaSUS)
def obter_mov_dps(id_dps: int, session: Session = Depends(get_session)):
    """Obtém uma movimentação específica"""
    mov = session.get(DistribuidorParaSUS, id_dps)
    if not mov:
        raise HTTPException(status_code=404, detail="Movimentação não encontrada")
    return mov


@router.post("/distribuidor-sus", response_model=DistribuidorParaSUS, status_code=status.HTTP_201_CREATED)
def criar_mov_dps(
    id_distribuidor: int,
    id_sus: int,
    id_lote: int,
    session: Session = Depends(get_session)
):
    """Cria uma nova movimentação Distribuidor → SUS"""
    envio = DistribuidorParaSUS(
        id_distribuidor=id_distribuidor,
        id_sus=id_sus,
        id_lote=id_lote,
        data_envio=datetime.now(),
        status="Em trânsito"
    )
    session.add(envio)
    session.commit()
    session.refresh(envio)
    return envio


@router.put("/distribuidor-sus/{id_dps}", response_model=DistribuidorParaSUS)
def atualizar_mov_dps(id_dps: int, status: str, session: Session = Depends(get_session)):
    """Atualiza o status de uma movimentação Distribuidor → SUS"""
    mov = session.get(DistribuidorParaSUS, id_dps)
    if not mov:
        raise HTTPException(status_code=404, detail="Movimentação não encontrada")

    mov.status = status
    session.add(mov)
    session.commit()
    session.refresh(mov)
    return mov


@router.delete("/distribuidor-sus/{id_dps}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_mov_dps(id_dps: int, session: Session = Depends(get_session)):
    """Deleta uma movimentação Distribuidor → SUS"""
    mov = session.get(DistribuidorParaSUS, id_dps)
    if not mov:
        raise HTTPException(status_code=404, detail="Movimentação não encontrada")
    session.delete(mov)
    session.commit()
    return {"message": "Movimentação excluída com sucesso"}


@router.post("/distribuidor-sus/{id_dps}/receber")
def confirmar_recebimento_dps(id_dps: int, session: Session = Depends(get_session)):
    """Confirma recebimento do lote pelo SUS"""
    mov = session.get(DistribuidorParaSUS, id_dps)
    if not mov:
        raise HTTPException(status_code=404, detail="Movimentação não encontrada")

    mov.data_recebimento = datetime.now()
    mov.status = "Recebido"
    session.add(mov)
    session.commit()
    return {"message": "Recebimento confirmado com sucesso", "movimentacao": mov}


# ==========================================================
#  SUS → UBS
# ==========================================================

@router.get("/sus-ubs", response_model=List[SUSParaUBS])
def listar_mov_spu(session: Session = Depends(get_session)):
    return session.exec(select(SUSParaUBS)).all()


@router.get("/sus-ubs/{id_spu}", response_model=SUSParaUBS)
def obter_mov_spu(id_spu: int, session: Session = Depends(get_session)):
    mov = session.get(SUSParaUBS, id_spu)
    if not mov:
        raise HTTPException(status_code=404, detail="Movimentação não encontrada")
    return mov


@router.post("/sus-ubs", response_model=SUSParaUBS, status_code=status.HTTP_201_CREATED)
def criar_mov_spu(
    id_sus: int,
    id_ubs: int,
    id_lote: int,
    session: Session = Depends(get_session)
):
    envio = SUSParaUBS(
        id_sus=id_sus,
        id_ubs=id_ubs,
        id_lote=id_lote,
        data_envio=datetime.now(),
        status="Em trânsito"
    )
    session.add(envio)
    session.commit()
    session.refresh(envio)
    return envio


@router.put("/sus-ubs/{id_spu}", response_model=SUSParaUBS)
def atualizar_mov_spu(id_spu: int, status: str, session: Session = Depends(get_session)):
    mov = session.get(SUSParaUBS, id_spu)
    if not mov:
        raise HTTPException(status_code=404, detail="Movimentação não encontrada")

    mov.status = status
    session.add(mov)
    session.commit()
    session.refresh(mov)
    return mov


@router.delete("/sus-ubs/{id_spu}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_mov_spu(id_spu: int, session: Session = Depends(get_session)):
    mov = session.get(SUSParaUBS, id_spu)
    if not mov:
        raise HTTPException(status_code=404, detail="Movimentação não encontrada")
    session.delete(mov)
    session.commit()
    return {"message": "Movimentação excluída com sucesso"}


@router.post("/sus-ubs/{id_spu}/receber")
def confirmar_recebimento_spu(id_spu: int, session: Session = Depends(get_session)):
    mov = session.get(SUSParaUBS, id_spu)
    if not mov:
        raise HTTPException(status_code=404, detail="Movimentação não encontrada")

    mov.data_recebimento = datetime.now()
    mov.status = "Recebido"
    session.add(mov)
    session.commit()
    return {"message": "Recebimento confirmado com sucesso", "movimentacao": mov}


# ==========================================================
#  UBS → PACIENTE
# ==========================================================

@router.get("/ubs-paciente", response_model=List[UBSParaPaciente])
def listar_mov_upp(session: Session = Depends(get_session)):
    return session.exec(select(UBSParaPaciente)).all()


@router.get("/ubs-paciente/{id_upp}", response_model=UBSParaPaciente)
def obter_mov_upp(id_upp: int, session: Session = Depends(get_session)):
    mov = session.get(UBSParaPaciente, id_upp)
    if not mov:
        raise HTTPException(status_code=404, detail="Movimentação não encontrada")
    return mov


@router.post("/ubs-paciente", response_model=UBSParaPaciente, status_code=status.HTTP_201_CREATED)
def criar_mov_upp(
    id_ubs: int,
    id_paciente: int,
    id_lote: int,
    session: Session = Depends(get_session)
):
    envio = UBSParaPaciente(
        id_ubs=id_ubs,
        id_paciente=id_paciente,
        id_lote=id_lote,
        data_envio=datetime.now(),
        status="Em trânsito"
    )
    session.add(envio)
    session.commit()
    session.refresh(envio)
    return envio


@router.put("/ubs-paciente/{id_upp}", response_model=UBSParaPaciente)
def atualizar_mov_upp(id_upp: int, status: str, session: Session = Depends(get_session)):
    mov = session.get(UBSParaPaciente, id_upp)
    if not mov:
        raise HTTPException(status_code=404, detail="Movimentação não encontrada")

    mov.status = status
    session.add(mov)
    session.commit()
    session.refresh(mov)
    return mov


@router.delete("/ubs-paciente/{id_upp}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_mov_upp(id_upp: int, session: Session = Depends(get_session)):
    mov = session.get(UBSParaPaciente, id_upp)
    if not mov:
        raise HTTPException(status_code=404, detail="Movimentação não encontrada")
    session.delete(mov)
    session.commit()
    return {"message": "Movimentação excluída com sucesso"}


@router.post("/ubs-paciente/{id_upp}/receber")
def confirmar_recebimento_upp(id_upp: int, session: Session = Depends(get_session)):
    mov = session.get(UBSParaPaciente, id_upp)
    if not mov:
        raise HTTPException(status_code=404, detail="Movimentação não encontrada")

    mov.data_recebimento = datetime.now()
    mov.status = "Entregue ao paciente"
    session.add(mov)
    session.commit()
    return {"message": "Entrega confirmada com sucesso", "movimentacao": mov}