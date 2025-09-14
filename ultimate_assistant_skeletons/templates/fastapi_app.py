"""
fastapi_app.py – Minimale FastAPI-Anwendung

Dieses Template bietet einen schnellen Einstieg in eine FastAPI-App mit
Healthcheck-Endpunkt. Weitere Routen können nach Bedarf ergänzt werden.
"""
from fastapi import FastAPI

app = FastAPI(title="FastAPI Skeleton")


@app.get("/health", tags=["health"])
async def health() -> dict:
    return {"status": "ok"}


# Beispiel: weitere Endpunkte definieren
# @app.post("/items", tags=["items"])
# async def create_item(item: ItemModel) -> ItemModel:
#     ...
