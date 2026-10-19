# GateWay CIP

Mini backend en FastAPI para recibir lecturas del PLC, normalizarlas y
guardarlas en SQLite.

## 1. Crear el entorno virtual

En PowerShell, desde esta carpeta:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-api.txt
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

Enviar una lectura del PLC con `POST /api/dato`. El cuerpo incluye los campos
del PLC mapeados al contrato de la API; `nivel_t_residual` es opcional porque
no aparece en el payload observado. Los ciclos `0`, `1` y `2` se guardan como
`PRE-ENJUAGUE`, `ENJABONADO` y `ENJUAGUE`, respectivamente:

```powershell
Invoke-RestMethod -Method Post `
	-Uri http://localhost:8010/api/dato `
	-ContentType "application/json" `
	-Body '{"temperatura":34.7,"ciclo":1,"nivel_cabina":false,"estado_bomba_drenado":false,"estado_bomba_dosificadora":false,"estado_resistencia":false,"motor_agitacion":false}'
```

Los estados de equipo aceptan booleanos JSON (`true`/`false`), `1`/`0` o
textos `ON`/`OFF` y `TRUE`/`FALSE`, sin distinguir mayusculas. Se guardan
normalizados como `ON`/`OFF`. La señal `nivel_cabina` del PLC es invertida:
`true`, `1` o `"TRUE"` significa `VACIO`; `false`, `0` o `"FALSE"` significa
`LLENO`. La API guarda ese nivel como `VACIO`/`LLENO`. Si no se manda
`nivel_t_residual`, queda como `SIN DATO`.

En un nodo **Function** de Node-RED, mapea las variables recibidas del S7 al
contrato HTTP y conecta la salida con un nodo **HTTP request** configurado como
`POST http://34.226.194.178:8010/api/dato`, con cuerpo JSON. Este ejemplo
acepta estados del PLC como booleanos, `0`/`1` o texto `ON`/`OFF`/`TRUE`/`FALSE`:

```javascript
const plc = msg.payload;

function estadoBooleano(valor, nombre) {
	if (typeof valor === "boolean") return valor;
	if (typeof valor === "number" && (valor === 0 || valor === 1)) {
		return valor === 1;
	}
	if (typeof valor === "string") {
		switch (valor.trim().toUpperCase()) {
			case "1":
			case "ON":
			case "TRUE":
				return true;
			case "0":
			case "OFF":
			case "FALSE":
				return false;
		}
	}
	throw new Error(nombre + " debe ser 0/1, ON/OFF o TRUE/FALSE");
}

function nivelCabinaBooleano(valor) {
	if (typeof valor === "boolean") return valor;
	if (typeof valor === "number" && (valor === 0 || valor === 1)) {
		return valor === 1;
	}
	if (typeof valor === "string") {
		switch (valor.trim().toUpperCase()) {
			case "TRUE":
			case "1":
			case "VACIO":
				return true;
			case "FALSE":
			case "0":
			case "LLENO":
				return false;
		}
	}
	throw new Error("Nivel_Cabina debe ser true/false, 1/0 o VACIO/LLENO");
}

try {
	if (!plc || typeof plc !== "object") {
		throw new Error("msg.payload no contiene el objeto del PLC");
	}
	if (plc.Temperatura === undefined || plc.Temperatura === null || plc.Temperatura === "") {
		throw new Error("Falta Temperatura");
	}
	if (plc.Nivel_Cabina === undefined || plc.Nivel_Cabina === null || plc.Nivel_Cabina === "") {
		throw new Error("Falta Nivel_Cabina");
	}
	if (plc.ciclo === undefined || plc.ciclo === null || plc.ciclo === "") {
		throw new Error("Falta ciclo");
	}

	const temperatura = Number(plc.Temperatura);
	if (!Number.isFinite(temperatura)) {
		throw new Error("Temperatura no es numerica");
	}

	const ciclo = String(plc.ciclo).trim();
	if (!["0", "1", "2", "PRE-ENJUAGUE", "PRE ENJUAGUE", "ENJABONADO", "ENJUAGUE"]
		.some(valor => valor === ciclo.toUpperCase())) {
		throw new Error("ciclo debe ser 0, 1 o 2");
	}
	const nivelCabina = nivelCabinaBooleano(plc.Nivel_Cabina);
	node.warn("Nivel_Cabina recibido=" + JSON.stringify(plc.Nivel_Cabina) +
		" tipo=" + typeof plc.Nivel_Cabina + " enviado=" + nivelCabina);

	msg.method = "POST";
	msg.url = "http://34.226.194.178:8010/api/dato";
	msg.headers = { "Content-Type": "application/json" };
	msg.payload = {
		temperatura: temperatura,
		ciclo: ciclo,
		nivel_cabina: nivelCabina,
		estado_bomba_drenado: estadoBooleano(plc.Estado_bomba_drenado, "Estado_bomba_drenado"),
		estado_bomba_dosificadora: estadoBooleano(plc.Estado_bomba_dosificadora, "Estado_bomba_dosificadora"),
		estado_resistencia: estadoBooleano(plc.Estado_resistencia, "Estado_resistencia"),
		motor_agitacion: estadoBooleano(plc.motor_agitacion, "motor_agitacion")
	};
	return msg;
} catch (error) {
	node.error("No se envio lectura a FastAPI: " + error.message, msg);
	return null;
}
```

El ejemplo corresponde al objeto visto en Debug: `Temperatura`, `Nivel_Cabina`,
`Estado_bomba_drenado`, `Estado_bomba_dosificadora`, `Estado_resistencia`,
`ciclo` y `motor_agitacion`. Si el nodo S7 entrega los valores dentro de otra propiedad (por ejemplo,
`msg.payload.values`), cambia `const plc = msg.payload;` por
`const plc = msg.payload.values;`. Confirma las rutas viendo el mensaje completo
en un nodo **Debug**. No uses `Boolean(valor)` para convertir valores del PLC:
en JavaScript, `Boolean("0")` y `Boolean("false")` dan `true` porque son
strings no vacios.

Conecta el Function directamente al nodo **HTTP request**. Configura el nodo
para usar `msg.method` y `msg.url` (o fija el metodo `POST` y la misma URL en el
nodo), y selecciona retorno como objeto JSON. Conecta su salida a un nodo
**Debug** configurado para mostrar el mensaje completo. Una respuesta exitosa
tiene estado `201`; revisa
`msg.statusCode` y `msg.payload`. Un `422` indica que falta un campo, un nivel
llego vacio o un ciclo/estado tiene un valor no aceptado. Si recibes un error de
conexion o timeout, comprueba IP publica, puerto `8010` y Security Group de AWS.

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

## 4. Consumir la API desde Flutter

La API entrega JSON. `GET /api/dato` devuelve la lectura mas reciente y
`GET /api/datos` devuelve el historial paginado. En el proyecto Flutter agrega
el cliente HTTP:

```bash
flutter pub add http
```

Usa la IP publica de EC2 como base URL. No uses `localhost` desde el telefono
ni desde el emulador Android: `localhost` apuntaria al propio dispositivo. En
el emulador Android puedes usar `10.0.2.2` si la API corre en tu PC; para EC2,
usa la IP publica o el dominio:

```dart
const apiBaseUrl = 'http://34.226.194.178:8010';
```

El modelo Dart para la respuesta:

```dart
class Lectura {
	const Lectura({
		required this.id,
		required this.fechaHora,
		required this.temperatura,
		required this.ciclo,
		required this.nivelCabina,
		required this.nivelTResidual,
		required this.estadoBombaDrenado,
		required this.estadoBombaDosificadora,
		required this.estadoResistencia,
		required this.motorAgitacion,
	});

	final int id;
	final DateTime fechaHora;
	final double temperatura;
	final String ciclo;
	final String nivelCabina;
	final String nivelTResidual;
	final String estadoBombaDrenado;
	final String estadoBombaDosificadora;
	final String estadoResistencia;
	final String motorAgitacion;

	factory Lectura.fromJson(Map<String, dynamic> json) {
		return Lectura(
			id: json['id'] as int,
			fechaHora: DateTime.parse(json['fecha_hora'] as String),
			temperatura: (json['temperatura'] as num).toDouble(),
			ciclo: json['ciclo'] as String,
			nivelCabina: json['nivel_cabina'] as String,
			nivelTResidual: json['nivel_t_residual'] as String,
			estadoBombaDrenado: json['estado_bomba_drenado'] as String,
			estadoBombaDosificadora: json['estado_bomba_dosificadora'] as String,
			estadoResistencia: json['estado_resistencia'] as String,
			motorAgitacion: json['motor_agitacion'] as String,
		);
	}
}
```

Cliente para consultar la ultima lectura y el historial:

```dart
import 'dart:convert';

import 'package:http/http.dart' as http;

const apiBaseUrl = 'http://34.226.194.178:8010';

class CipApi {
	CipApi({http.Client? client}) : _client = client ?? http.Client();

	final http.Client _client;

	Future<Lectura> obtenerUltimaLectura() async {
		final uri = Uri.parse('$apiBaseUrl/api/dato');
		final response = await _client
				.get(uri)
				.timeout(const Duration(seconds: 10));

		if (response.statusCode != 200) {
			throw Exception('Error ${response.statusCode}: ${response.body}');
		}

		return Lectura.fromJson(
			jsonDecode(response.body) as Map<String, dynamic>,
		);
	}

	Future<List<Lectura>> obtenerHistorial({
		int limit = 100,
		int offset = 0,
	}) async {
		final uri = Uri.parse('$apiBaseUrl/api/datos').replace(
			queryParameters: {'limit': '$limit', 'offset': '$offset'},
		);
		final response = await _client
				.get(uri)
				.timeout(const Duration(seconds: 10));

		if (response.statusCode != 200) {
			throw Exception('Error ${response.statusCode}: ${response.body}');
		}

		final body = jsonDecode(response.body) as Map<String, dynamic>;
		final registros = body['registros'] as List<dynamic>;
		return registros
				.map((item) => Lectura.fromJson(item as Map<String, dynamic>))
				.toList();
	}
}
```

Uso desde una pantalla Flutter para mostrar la lectura mas reciente:

```dart
final api = CipApi();

FutureBuilder<Lectura>(
	future: api.obtenerUltimaLectura(),
	builder: (context, snapshot) {
		if (snapshot.hasError) {
			return Text('No se pudo cargar la lectura: ${snapshot.error}');
		}
		if (!snapshot.hasData) {
			return const CircularProgressIndicator();
		}

		final lectura = snapshot.data!;
		return Text(
			'${lectura.temperatura} °C | ${lectura.ciclo} | '
			'Agitacion: ${lectura.motorAgitacion}',
		);
	},
)
```

`FutureBuilder` consulta al construir la pantalla; para actualizar mientras la
pantalla esta abierta, vuelve a solicitar `GET /api/dato` con un `Timer.periodic`
(por ejemplo, cada 2 segundos) y cancela el timer en `dispose()`. Esto es
sondeo HTTP, no WebSocket: el endpoint devuelve el ultimo dato disponible cada
vez que se consulta.

La API actual usa HTTP sin TLS para pruebas. Para publicar una app Flutter,
configura HTTPS (por ejemplo, con Nginx y un certificado) antes de distribuirla.

## 5. Dashboard de consumo con Streamlit

El dashboard consulta `GET /api/dato` para mostrar el ciclo actual, la
temperatura, los niveles y los equipos; `GET /api/datos` alimenta la curva y el
historial. La direccion de la API se configura de forma privada y no se muestra
ni se puede editar desde la pantalla. El panel de preferencias solo permite
cambiar el refresco y el numero de registros consultados. No modifica ni
reemplaza la API FastAPI.

Instala las dependencias del dashboard en el entorno virtual de tu PC:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dashboard.txt
```

La URL por defecto apunta a EC2. Para sobrescribirla localmente y arrancar
Streamlit en el puerto `8501`:

```powershell
$env:API_BASE_URL="http://34.226.194.178:8010"
python -m streamlit run streamlit_app.py --server.port 8501
```

Abre `http://localhost:8501`. En la barra lateral puedes ajustar el intervalo
de refresco (2 a 60 segundos) y la cantidad de lecturas historicas. Tambien
puedes crear `.streamlit/secrets.toml` local copiando
`.streamlit/secrets.toml.example`; este archivo esta excluido de Git.

Streamlit hace las peticiones desde el proceso Python, no directamente desde
el navegador; por eso no requiere habilitar CORS en FastAPI. La maquina donde
ejecutas Streamlit debe poder acceder al puerto `8010` de la API.

Si decides alojar tambien el dashboard en EC2, inicia Streamlit escuchando en
todas las interfaces y apunta a la API local:

```bash
API_BASE_URL="http://127.0.0.1:8010" \
python -m streamlit run streamlit_app.py --server.address 0.0.0.0 --server.port 8501
```

En ese caso abre `8501/tcp` en el Security Group solo para las IP que necesiten
ver el dashboard. Para uso real, publica Streamlit detras de HTTPS y evita
exponerlo directamente a todo internet.

Las ilustraciones actuales de motor, bombas y resistencia son SVG originales
incluidos en el codigo, y cambian de color segun el estado del equipo. Si se
sustituyen por iconos de Flaticon, descarga los archivos en el proyecto y agrega
la atribucion que indique Flaticon para cada autor/icono.

### Desplegar en Streamlit Community Cloud

1. Sube el repositorio a GitHub. No agregues `Facturaciones.pem`,
	`gateway_cip.db`, `.venv` ni `.streamlit/secrets.toml`; estan excluidos por
	`.gitignore`. Primero confirma que todos los cambios de despliegue esten
	guardados y subidos a la rama elegida: Community Cloud no lee tus cambios
	locales.
2. Entra a [share.streamlit.io](https://share.streamlit.io/) y conecta GitHub.
3. Crea una app indicando el repositorio, la rama que contiene los cambios y
	el archivo principal `streamlit_app.py`.
4. En **Advanced settings / Secrets**, configura la direccion de FastAPI como
	TOML:

	```toml
	API_BASE_URL = "http://34.226.194.178:8010"
	```

5. Pulsa **Deploy**. Community Cloud instala las dependencias del
	`requirements.txt` de la raiz y publica el dashboard en una URL de
	`streamlit.app`.

La configuracion de Secrets no aparece en la interfaz ni necesita guardarse en
GitHub. `.streamlit/secrets.toml.example` sirve como plantilla local; no subas
el archivo real `secrets.toml`.

**Importante sobre la clave EC2:** `Facturaciones.pem` estuvo versionada en este
repositorio. Se ha preparado su eliminacion del proximo commit sin borrar la
copia local, pero eso no quita la clave de commits anteriores. Antes de hacer
publico el repositorio, rota la clave SSH de la instancia y considera limpiar el
historial de Git; no basta con borrar el archivo en el ultimo commit.

#### Conectividad con EC2

Community Cloud debe poder alcanzar la API por el puerto `8010`. Verifica que la
direccion publica de EC2 siga siendo la correcta y que el Security Group permita
el trafico entrante desde el origen de red usado por la app de Streamlit. No
abras `8010` a todo internet sin autenticacion: el endpoint POST acepta y guarda
lecturas. Para un despliegue compartido, protege la API, limita el origen cuando
sea posible y configura HTTPS antes de distribuir el dashboard.

## 6. Ejecutar en AWS

En una instancia EC2, instala Python, copia el proyecto, crea el entorno
virtual y levanta el proceso con:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-api.txt
python -m uvicorn app:app --host 0.0.0.0 --port 8010
```

Abre el puerto TCP `8010` en el Security Group de la instancia. Para un
entorno productivo, ejecuta Uvicorn con `systemd` o detras de Nginx y no uses
`--reload`.

> En una sola instancia EC2, SQLite conserva el historial en el disco local.
> Si ejecutas varias instancias de la API, usa una base de datos compartida,
> como RDS o DynamoDB, en lugar del archivo SQLite local.