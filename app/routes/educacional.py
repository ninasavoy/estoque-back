from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import SQLModel, Session, select
from typing import List, Optional
from datetime import datetime
from models import ConteudoEducacional, Farmaceutica, Medicamento, User
from database import get_session
from auth.dependencies import get_current_user

router = APIRouter(prefix="/conteudo", tags=["Conteúdo Educacional"])


@router.get("/", response_model=List[ConteudoEducacional])
def listar_conteudos(session: Session = Depends(get_session)):
    return session.exec(select(ConteudoEducacional)).all()


@router.get("/{conteudo_id}", response_model=ConteudoEducacional)
def obter_conteudo(conteudo_id: int, session: Session = Depends(get_session)):
    
    conteudo = session.get(ConteudoEducacional, conteudo_id)
    if not conteudo:
        raise HTTPException(status_code=404, detail="Conteúdo não encontrado")
    return conteudo


@router.post("/", response_model=ConteudoEducacional)
def criar_conteudo(
    id_medicamento: int,
    titulo: str,
    tipo: str,
    conteudo: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    if current_user.tipo not in ["admin", "farmaceutica"]:
        raise HTTPException(status_code=403, detail="Acesso restrito a farmacêuticas e administradores")
    
    if not current_user.ativo:
        raise HTTPException(status_code=403, detail="Finalize seu cadastro")

    medicamento = session.get(Medicamento, id_medicamento)
    if not medicamento:
        raise HTTPException(status_code=404, detail="Medicamento não encontrado")

    if current_user.tipo == "farmaceutica":
        farmaceutica = session.exec(
            select(Farmaceutica).where(Farmaceutica.id_usuario == current_user.id)
        ).first()
        if not farmaceutica or medicamento.id_farmaceutica != farmaceutica.id_farmaceutica:
            raise HTTPException(status_code=403, detail="Você só pode criar conteúdo sobre seus próprios medicamentos")
        
    tipos_validos = ["doenca", "medicamento", "uso_correto", "efeitos_colaterais"]
    if tipo not in tipos_validos:
        raise HTTPException(status_code=400, detail=f"Tipo inválido. Use: {', '.join(tipos_validos)}")
    
    novo_conteudo = ConteudoEducacional(
        id_medicamento=id_medicamento,
        titulo=titulo,
        tipo=tipo,
        conteudo=conteudo,
        data_criacao=datetime.now()
    )
    session.add(novo_conteudo)
    session.commit()
    session.refresh(novo_conteudo)
    return novo_conteudo


@router.put("/{conteudo_id}", response_model=ConteudoEducacional)
def atualizar_conteudo(
    conteudo_id: int,
    titulo: Optional[str] = None,
    tipo: Optional[str] = None,
    conteudo: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    if current_user.tipo not in ["admin", "farmaceutica"]:
        raise HTTPException(status_code=403, detail="Acesso restrito a farmacêuticas e administradores")
    
    if not current_user.ativo:
        raise HTTPException(status_code=403, detail="Finalize seu cadastro")

    conteudo_obj = session.get(ConteudoEducacional, conteudo_id)
    if not conteudo_obj:
        raise HTTPException(status_code=404, detail="Conteúdo não encontrado")

    medicamento = session.get(Medicamento, conteudo_obj.id_medicamento)

    if current_user.tipo == "farmaceutica":
        farmaceutica = session.exec(
            select(Farmaceutica).where(Farmaceutica.id_usuario == current_user.id)
        ).first()
        if not farmaceutica or medicamento.id_farmaceutica != farmaceutica.id_farmaceutica:
            raise HTTPException(status_code=403, detail="Você só pode atualizar conteúdos dos seus próprios medicamentos")
        
    if titulo is not None:
        conteudo_obj.titulo = titulo
    if tipo is not None:
        tipos_validos = ["doenca", "medicamento", "uso_correto", "efeitos_colaterais"]
        if tipo not in tipos_validos:
            raise HTTPException(status_code=400, detail=f"Tipo inválido. Use: {', '.join(tipos_validos)}")
        conteudo_obj.tipo = tipo
    if conteudo is not None:
        conteudo_obj.conteudo = conteudo
    
    session.add(conteudo_obj)
    session.commit()
    session.refresh(conteudo_obj)
    return conteudo_obj

# ------------------------------
# Deletar conteúdo
# ------------------------------
@router.delete("/{conteudo_id}")
def deletar_conteudo(
    conteudo_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    if current_user.tipo not in ["admin", "farmaceutica"]:
        raise HTTPException(status_code=403, detail="Acesso restrito a farmacêuticas e administradores")
    
    if not current_user.ativo:
        raise HTTPException(status_code=403, detail="Finalize seu cadastro")

    conteudo_obj = session.get(ConteudoEducacional, conteudo_id)
    if not conteudo_obj:
        raise HTTPException(status_code=404, detail="Conteúdo não encontrado")

    medicamento = session.get(Medicamento, conteudo_obj.id_medicamento)

    if current_user.tipo == "farmaceutica":
        farmaceutica = session.exec(
            select(Farmaceutica).where(Farmaceutica.id_usuario == current_user.id)
        ).first()
        if not farmaceutica or medicamento.id_farmaceutica != farmaceutica.id_farmaceutica:
            raise HTTPException(status_code=403, detail="Você só pode deletar conteúdos dos seus próprios medicamentos")

    session.delete(conteudo_obj)
    session.commit()
    return {"message": "Conteúdo deletado com sucesso"}
