from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from typing import List
from auth.dependencies import get_current_user
from models import Farmaceutica, Medicamento
from database import get_session

router = APIRouter(prefix="/medicamentos", tags=["Medicamentos"])

# CREATE
# ////////////////////////////////////////////////////////////

@router.post("/", response_model=Medicamento)
def create_medicamento(medicamento: Medicamento, current_user = Depends(get_current_user), session: Session = Depends(get_session)):
    if current_user.tipo != "admin" and current_user.tipo != "farmaceutica":
        raise HTTPException(status_code=403, detail="Você não tem permissão para criar medicamentos")

    if current_user.tipo == "farmaceutica":
        farmaceutica = session.exec(
            select(Farmaceutica).where(Farmaceutica.id_usuario == current_user.id)
        ).first()

        if not farmaceutica:
            raise HTTPException(status_code=404, detail="Farmacêutica não encontrada")
        
        medicamento.id_farmaceutica = farmaceutica.id_farmaceutica

    session.add(medicamento)
    session.commit()
    session.refresh(medicamento)
    return medicamento


# ///////////////////////////////////////////////////////////


# READ
# ///////////////////////////////////////////////////////////

@router.get("/", response_model=List[Medicamento])
def list_medicamentos(session: Session = Depends(get_session), current_user = Depends(get_current_user)):
    if current_user.tipo != "admin" and current_user.tipo != "farmaceutica":
        raise HTTPException(status_code=403, detail="Você não tem permissão para criar medicamentos")

    medicamentos = session.exec(select(Medicamento)).all()
    if current_user.tipo == "farmaceutica":
        farmaceutica = session.exec(
            select(Farmaceutica).where(Farmaceutica.id_usuario == current_user.id)
        ).first()

        if not farmaceutica:
            raise HTTPException(status_code=404, detail="Farmacêutica não encontrada")
        
        medicamentos = session.exec(
            select(Medicamento).where(Medicamento.id_farmaceutica == farmaceutica.id_farmaceutica)
        ).all()
    
    return medicamentos


@router.get("/{medicamento_id}", response_model=Medicamento)
def get_medicamento(medicamento_id: int, session: Session = Depends(get_session), current_user = Depends(get_current_user)):
    if current_user.tipo != "admin" and current_user.tipo != "farmaceutica":
        raise HTTPException(status_code=403, detail="Você não tem permissão para criar medicamentos")

    medicamento = session.get(Medicamento, medicamento_id)
    if not medicamento:
        raise HTTPException(status_code=404, detail="Medicamento não encontrado")
    
    if current_user.tipo == "farmaceutica":
        farmaceutica = session.exec(
            select(Farmaceutica).where(Farmaceutica.id_usuario == current_user.id)
        ).first()

        if not farmaceutica:
            raise HTTPException(status_code=404, detail="Farmacêutica não encontrada")

        if medicamento.id_farmaceutica != farmaceutica.id_farmaceutica:
            raise HTTPException(status_code=403, detail="Você não tem acesso a este medicamento")

    return medicamento


@router.get("/farmaceutica/{farmaceutica_id}", response_model=List[Medicamento])
def list_medicamentos_by_farmaceutica(
    farmaceutica_id: int, 
    session: Session = Depends(get_session), 
    current_user = Depends(get_current_user)
):
    if current_user.tipo != "admin":
        raise HTTPException(status_code=403, detail="Você não tem permissão para ver estes medicamentos")

    medicamentos = session.exec(
        select(Medicamento).where(Medicamento.id_farmaceutica == farmaceutica_id)
    ).all()
    return medicamentos


@router.get("/alto_custo/", response_model=List[Medicamento])
def list_medicamentos_alto_custo(
    session: Session = Depends(get_session), 
    current_user = Depends(get_current_user)
):
    if current_user.tipo != "admin" and current_user.tipo != "farmaceutica":
        raise HTTPException(status_code=403, detail="Você não tem permissão para ver estes medicamentos")

    medicamentos = session.exec(
        select(Medicamento).where(Medicamento.alto_custo == True)
    ).all() 

    if current_user.tipo == "farmaceutica":
        farmaceutica = session.exec(
            select(Farmaceutica).where(Farmaceutica.id_usuario == current_user.id)
        ).first()

        if not farmaceutica:
            raise HTTPException(status_code=404, detail="Farmacêutica não encontrada")
        
        medicamentos = session.exec(
            select(Medicamento).where(
                Medicamento.alto_custo == True,
                Medicamento.id_farmaceutica == farmaceutica.id_farmaceutica
            )
        ).all()
    
    return medicamentos


# ///////////////////////////////////////////////////////////


# UPDATE
# ///////////////////////////////////////////////////////////

@router.put("/{medicamento_id}", response_model=Medicamento)
def update_medicamento(
    medicamento_id: int, 
    medicamento: Medicamento, 
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    if current_user.tipo != "admin" and current_user.tipo != "farmaceutica":
        raise HTTPException(status_code=403, detail="Você não tem permissão para alterar medicamentos")

    db_medicamento = session.get(Medicamento, medicamento_id)
    if not db_medicamento:
        raise HTTPException(status_code=404, detail="Medicamento não encontrado")
    
    if current_user.tipo == "farmaceutica":
        farmaceutica = session.exec(
            select(Farmaceutica).where(Farmaceutica.id_usuario == current_user.id)
        ).first()

        if not farmaceutica:
            raise HTTPException(status_code=404, detail="Farmacêutica não encontrada")

        if db_medicamento.id_farmaceutica != farmaceutica.id_farmaceutica:
            raise HTTPException(status_code=403, detail="Você não tem permissão para alterar este medicamento")

    medicamento_data = medicamento.model_dump(exclude_unset=True, exclude={"id_medicamento"})
    for key, value in medicamento_data.items():
        setattr(db_medicamento, key, value)
    
    session.add(db_medicamento)
    session.commit()
    session.refresh(db_medicamento)
    
    return db_medicamento

# ///////////////////////////////////////////////////////////


# DELETE
# ///////////////////////////////////////////////////////////

@router.delete("/{medicamento_id}")
def delete_medicamento(medicamento_id: int, session: Session = Depends(get_session), current_user = Depends(get_current_user)):
    medicamento = session.get(Medicamento, medicamento_id)
    if not medicamento:
        raise HTTPException(status_code=404, detail="Medicamento não encontrado")

    if current_user.tipo != "admin" and current_user.tipo != "farmaceutica":
        raise HTTPException(status_code=403, detail="Você não tem permissão para deletar medicamentos")

    if current_user.tipo == "farmaceutica":
        farmaceutica = session.exec(
            select(Farmaceutica).where(Farmaceutica.id_usuario == current_user.id)
        ).first()

        if not farmaceutica:
            raise HTTPException(status_code=404, detail="Farmacêutica não encontrada")

        if medicamento.id_farmaceutica != farmaceutica.id_farmaceutica:
            raise HTTPException(
                status_code=403,
                detail="Você não tem permissão para deletar este medicamento"
            )

    session.delete(medicamento)
    session.commit()
    return {"message": "Medicamento deletado com sucesso"}