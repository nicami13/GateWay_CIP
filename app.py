from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


app = FastAPI(
    title="Gateway CIP API",
    description="Mini backend para recibir datos desde un boton.",
    version="1.0.0",
)


class DatoEntrada(BaseModel):
    dato: str = Field(..., min_length=1, max_length=500)


class RespuestaDato(BaseModel):
    mensaje: str
    dato: str


ultimo_dato: str | None = None


@app.get("/", tags=["salud"])
def raiz() -> dict[str, str]:
    return {"mensaje": "Gateway CIP API activa"}


@app.get("/api/dato", response_model=RespuestaDato, tags=["dato"])
def obtener_dato() -> RespuestaDato:
    if ultimo_dato is None:
        raise HTTPException(status_code=404, detail="Todavia no hay datos recibidos")

    return RespuestaDato(mensaje="Ultimo dato recibido", dato=ultimo_dato)


@app.post("/api/dato", response_model=RespuestaDato, status_code=201, tags=["dato"])
def recibir_dato(entrada: DatoEntrada) -> RespuestaDato:
    global ultimo_dato
    ultimo_dato = entrada.dato

    return RespuestaDato(mensaje="Dato recibido correctamente", dato=entrada.dato)
