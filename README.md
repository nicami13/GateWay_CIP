# GateWay CIP

Mini backend en FastAPI para recibir lecturas del PLC, normalizarlas y
guardarlas en SQLite.

## 1. Crear el entorno virtual

En PowerShell, desde esta carpeta:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Si PowerShell bloquea la activacion del entorno, ejecuta una vez:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

## 2. Levantar la API

El puerto recomendado es `8010`, porque `8000` ya esta ocupado por tu otra
API:

```powershell
python -m uvicorn app:app --host 0.0.0.0 --port 8010 --reload
```

La API quedara disponible en `http://localhost:8010` y la documentacion
interactiva en `http://localhost:8010/docs`.

Para usar otro puerto sin modificar archivos:

```powershell
$env:PORT="8011"
python -m uvicorn app:app --host 0.0.0.0 --port $env:PORT --reload
```

## 3. Peticiones

Enviar una lectura del PLC con `POST /api/dato`:

```powershell
Invoke-RestMethod -Method Post `
	-Uri http://localhost:8010/api/dato `
	-ContentType "application/json" `
	-Body '{"temperatura":52.4,"ciclo":2,"nivel_cabina":"alto","nivel_t_residual":"BAJO","estado_bomba_drenado":true,"estado_bomba_dosificadora":false,"estado_resistencia":true,"moto_agitacion":false}'
```

Los ciclos `1`, `2` y `3` se guardan como `PRE-ENJUAGUE`, `ENJABONADO` y
`ENJUAGUE`. Los estados aceptan booleanos JSON (`true`/`false`), `1`/`0` o
textos `ON`/`OFF` y `TRUE`/`FALSE`, sin distinguir mayusculas. Se guardan
normalizados como `ON`/`OFF`; los niveles tambien se convierten a mayusculas.

Consultar la ultima lectura con `GET /api/dato`:

```powershell
Invoke-RestMethod -Method Get -Uri http://localhost:8010/api/dato
```

Consultar historial con `GET /api/datos`. Acepta paginacion con `limit` (1 a
1000, por defecto 100) y `offset` (por defecto 0), por ejemplo:

```powershell
Invoke-RestMethod -Method Get -Uri "http://localhost:8010/api/datos?limit=100&offset=0"
```

Las lecturas quedan persistidas en `gateway_cip.db`, incluso al reiniciar la
API. Tambien puedes probar las rutas desde `/docs`.

## 4. Ejecutar en AWS

En una instancia EC2, instala Python, copia el proyecto, crea el entorno
virtual y levanta el proceso con:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app:app --host 0.0.0.0 --port 8010
```

Abre el puerto TCP `8010` en el Security Group de la instancia. Para un
entorno productivo, ejecuta Uvicorn con `systemd` o detras de Nginx y no uses
`--reload`.

> En una sola instancia EC2, SQLite conserva el historial en el disco local.
> Si ejecutas varias instancias de la API, usa una base de datos compartida,
> como RDS o DynamoDB, en lugar del archivo SQLite local.