from fastapi import FastAPI
from app.routes.webhook import router as webhook_router
from app.config.db_config import db

app = FastAPI()

app.include_router(webhook_router)


@app.on_event("startup")
async def startup():
    """
    Ejecuta código automáticamente cuando el servidor arranca.
    Es como un "gancho" de inicio.
    Lo usamos solo para verificar que PostgreSQL conecta bien al arrancar.
    """
    await db.check_connection()
