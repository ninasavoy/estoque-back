from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import create_db_and_tables
from routes import (
    user,   
    farmaceutica,
    medicamento,
    lote,
    distribuidor,
    feedback,
    sus,
    ubs,
    paciente,
    dashboard,
    auth,
    admin, 
    educacional,
)
from contextlib import asynccontextmanager

# Lifespan para startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Código de startup
    create_db_and_tables()
    yield
    # Código de shutdown (opcional)
    # Por exemplo: fechar conexões, limpar recursos, etc.

# Criar aplicação FastAPI
app = FastAPI(
    title="Sistema de Gestão de Medicamentos",
    description="API REST para gerenciamento de medicamentos",
    version="1.0.0",
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar todos os routers
app.include_router(user.router)
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(farmaceutica.router)
app.include_router(medicamento.router)
app.include_router(lote.router)
app.include_router(distribuidor.router)
app.include_router(sus.router)
app.include_router(ubs.router)
app.include_router(paciente.router)
app.include_router(feedback.router)
app.include_router(dashboard.router)
app.include_router(educacional.router)

@app.get("/")
def read_root():
    return {
        "message": "Sistema de Gestão de Medicamentos",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
