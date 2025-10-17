from fastapi import FastAPI
from sqlmodel import SQLModel
from app.database import engine
from app.models import medicamento, farmaceutica, lote, paciente, ubs, sus, feedback, movimentacao

app = FastAPI(title="Sistema de Gestão de Estoque de Medicamentos")

@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)

@app.get("/")
def root():
    return {"status": "API em funcionamento"}
