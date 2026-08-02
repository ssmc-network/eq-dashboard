from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routes import api, ui

app = FastAPI(title="EQ Dashboard")

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(ui.router)
app.include_router(api.router, prefix="/api")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
