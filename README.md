# GateWay CIP

Mini backend en FastAPI para recibir un dato desde un boton mediante `POST` y
consultar el ultimo dato recibido mediante `GET`.

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

Enviar el dato del boton:

```powershell
Invoke-RestMethod -Method Post `
	-Uri http://localhost:8010/api/dato `
	-ContentType "application/json" `
	-Body '{"dato":"boton-encendido"}'
```

Consultar el ultimo dato recibido:

```powershell
Invoke-RestMethod -Method Get -Uri http://localhost:8010/api/dato
```

Tambien puedes probarlas desde `/docs`.

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

> Nota: este ejemplo guarda el ultimo dato en memoria. Al reiniciar la API o
> tener varias instancias, el valor se pierde; para AWS conviene persistirlo
> en DynamoDB, RDS o Redis.