import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field


app = FastAPI(
    title="Gateway CIP API",
    description="Mini backend para recibir datos desde un boton.",
    version="1.0.0",
)


class DatoEntrada(BaseModel):
    temperatura: float
    ciclo: Any = Field(...)
    nivel_cabina: str = Field(..., min_length=1)
    nivel_t_residual: str = Field(..., min_length=1)
    estado_bomba_drenado: Any = Field(...)
    estado_bomba_dosificadora: Any = Field(...)
    estado_resistencia: Any = Field(...)
    motor_agitacion: Any = Field(...)


DB_PATH = Path(__file__).with_name("gateway_cip.db")


def conectar_db() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def inicializar_db() -> None:
    with conectar_db() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS lecturas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha_hora TEXT NOT NULL,
                temperatura REAL NOT NULL,
                ciclo TEXT NOT NULL,
                nivel_cabina TEXT NOT NULL,
                nivel_t_residual TEXT NOT NULL,
                estado_bomba_drenado TEXT NOT NULL,
                estado_bomba_dosificadora TEXT NOT NULL,
                estado_resistencia TEXT NOT NULL,
                motor_agitacion TEXT NOT NULL
            )
            """
        )


def normalizar_ciclo(valor: Any) -> str:
    ciclos = {
        "1": "PRE-ENJUAGUE",
        "2": "ENJABONADO",
        "3": "ENJUAGUE",
    }
    nombres = {
        "PRE-ENJUAGUE": "PRE-ENJUAGUE",
        "PRE ENJUAGUE": "PRE-ENJUAGUE",
        "ENJABONADO": "ENJABONADO",
        "ENJUAGUE": "ENJUAGUE",
    }
    if isinstance(valor, bool):
        raise ValueError("El ciclo debe ser 1, 2 o 3")
    if isinstance(valor, float) and valor.is_integer():
        valor = int(valor)
    texto = str(valor).strip().upper()
    if texto in ciclos:
        return ciclos[texto]
    if texto in nombres:
        return nombres[texto]
    raise ValueError("El ciclo debe ser 1, 2 o 3")


def normalizar_estado(valor: Any) -> str:
    if isinstance(valor, bool):
        return "ON" if valor else "OFF"
    if isinstance(valor, (int, float)) and valor in (0, 1):
        return "ON" if valor == 1 else "OFF"
    estados = {
        "TRUE": "ON",
        "1": "ON",
        "ON": "ON",
        "FALSE": "OFF",
        "0": "OFF",
        "OFF": "OFF",
    }
    estado = estados.get(str(valor).strip().upper())
    if estado is None:
        raise ValueError("El estado debe ser booleano, ON/OFF o true/false")
    return estado


def serializar_lectura(row: sqlite3.Row) -> dict[str, Any]:
    return dict(row)


inicializar_db()


@app.get("/", tags=["salud"])
def raiz() -> dict[str, str]:
    return {"mensaje": "Gateway CIP API activa"}


@app.get("/api/dato", tags=["datos"])
def obtener_ultimo_dato() -> dict[str, Any]:
    with conectar_db() as connection:
        row = connection.execute(
            "SELECT * FROM lecturas ORDER BY id DESC LIMIT 1"
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Todavia no hay datos recibidos")
    return serializar_lectura(row)


@app.get("/api/datos", tags=["datos"])
def obtener_historial(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> dict[str, Any]:
    with conectar_db() as connection:
        total = connection.execute("SELECT COUNT(*) FROM lecturas").fetchone()[0]
        rows = connection.execute(
            "SELECT * FROM lecturas ORDER BY id DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "registros": [serializar_lectura(row) for row in rows],
    }


@app.post("/api/dato", status_code=201, tags=["datos"])
def recibir_dato(entrada: DatoEntrada) -> dict[str, Any]:
    try:
        registro = {
            "fecha_hora": datetime.now(timezone.utc).isoformat(),
            "temperatura": entrada.temperatura,
            "ciclo": normalizar_ciclo(entrada.ciclo),
            "nivel_cabina": entrada.nivel_cabina.strip().upper(),
            "nivel_t_residual": entrada.nivel_t_residual.strip().upper(),
            "estado_bomba_drenado": normalizar_estado(entrada.estado_bomba_drenado),
            "estado_bomba_dosificadora": normalizar_estado(
                entrada.estado_bomba_dosificadora
            ),
            "estado_resistencia": normalizar_estado(entrada.estado_resistencia),
            "moto_agitacion": normalizar_estado(entrada.moto_agitacion),
        }
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    with conectar_db() as connection:
        cursor = connection.execute(
            """
            INSERT INTO lecturas (
                fecha_hora, temperatura, ciclo, nivel_cabina, nivel_t_residual,
                estado_bomba_drenado, estado_bomba_dosificadora,
                estado_resistencia, motor_agitacion
            ) VALUES (
                :fecha_hora, :temperatura, :ciclo, :nivel_cabina,
                :nivel_t_residual, :estado_bomba_drenado,
                :estado_bomba_dosificadora, :estado_resistencia, :moto_agitacion
            )
            """,
            registro,
        )
        registro["id"] = cursor.lastrowid

    return {"mensaje": "Dato guardado correctamente", **registro}
