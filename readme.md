# 📡 Instagram Webhook — FastAPI

Servicio backend para recibir y procesar eventos del webhook de Instagram/Meta usando **FastAPI** + **PostgreSQL** + **SQLAlchemy async**.

---

## 🚀 Setup del entorno

```bash
# Actualizar pip
python.exe -m pip install --upgrade pip

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
venv\Scripts\activate

# Instalar FastAPI con todas sus dependencias
pip install "fastapi[standard]"

# Guardar dependencias
pip freeze > requirements.txt
```

> 💡 **En VS Code:** `Ctrl + Shift + P` → `Python: Select Interpreter` → selecciona el intérprete del venv

---

## ▶️ Correr el servidor

```bash
fastapi dev app/main.py
```

---

## 🌐 Exponer con Ngrok

```bash
# Configurar token
ngrok config add-authtoken <tu_token>

# Exponer puerto 8000
ngrok http 8000
```

---

## 🏗️ Arquitectura del proyecto

```
project/
│
├── app/
│   ├── main.py                        # Entry point, instancia FastAPI
│   │
│   ├── routes/
│   │   └── webhook.py                 # Define rutas GET y POST /webhook
│   │
│   ├── controllers/
│   │   ├── webhook_checker.py         # Valida firma y challenge de Meta
│   │   └── webhook_processor.py      # Procesa eventos y persiste logs
│   │
│   ├── models/
│   │   └── webhook_log.py             # Modelo SQLAlchemy → tabla webhook_logs
│   │
│   ├── repositories/
│   │   └── webhook_log_repository.py  # Persiste logs en la DB (DIP)
│   │
│   └── config/
│       ├── settings.py                # Variables de entorno con Pydantic
│       ├── db_config.py               # Engine async + sesión + Base
│       └── webhook_validator.py       # Modelos Pydantic del payload
│
├── .env                               # Secrets (nunca al repo ⚠️)
├── .gitignore
└── requirements.txt
```

---

## ⚙️ Variables de entorno (`.env`)

```
Settings
├── App
│   ├── SECRET_KEY
│   ├── DEBUG
│   ├── HOST
│   └── PORT
│
├── Base de datos
│   ├── POSTGRES_USER
│   ├── POSTGRES_PASSWORD
│   ├── POSTGRES_HOST
│   ├── POSTGRES_PORT
│   └── POSTGRES_DB
│
└── Instagram
    ├── INSTAGRAM_VERIFY_TOKEN
    ├── INSTAGRAM_APP_SECRET
    ├── VERIFY_SIGNATURE
    ├── INSTAGRAM_ACCESS_TOKEN
    └── INSTAGRAM_BUSINESS_ACCOUNT_ID
```

---

## 🔁 Flujo — Verificación inicial del webhook (GET)

Cuando configuras el webhook en Meta, este hace un GET para verificar que el servidor es tuyo.

```
1. app.include_router(webhook_router)  →  le dice a FastAPI "estas rutas también existen"
2. Llega GET /webhook                  →  FastAPI busca la ruta que coincide y ejecuta su función
3. WebhookChecker.verify()             →  compara hub.verify_token con el tuyo
4. Responde con hub.challenge          →  Meta confirma el webhook ✅
```

```
Meta Platform
      │
      │  GET /webhook?hub.mode=subscribe
      │           &hub.verify_token=xxx
      │           &hub.challenge=yyy
      ▼
┌────────────────────────────────┐
│     Leer query params          │
│  (manual, no Query(...))       │
└────────────┬───────────────────┘
             │
             ▼
┌────────────────────────────────┐
│   ¿hub.verify_token válido?    │
└──────┬─────────────────┬───────┘
       │ NO              │ SÍ
       ▼                 ▼
   403 Forbidden    200 + hub.challenge
```

---

## 📨 Flujo — Recepción de eventos (POST)

```
Instagram Platform
      │
      │  POST /webhook
      │  { "object": "instagram", "entry": [...] }
      ▼
┌─────────────────────────────────────┐
│        Verificar firma              │
│   X-Hub-Signature-256 (HMAC SHA256) │
└────────────────┬────────────────────┘
                 │ ❌ → 403 Forbidden
                 │ ✅
                 ▼
┌─────────────────────────────────────┐
│        Validar object               │
│    ¿ object === "instagram" ?       │
└──────┬──────────────────────┬───────┘
       │ NO                   │ SÍ
       ▼                      ▼
  400 Bad Request      Persistir log en DB
                             │
                             ▼
                      Responder 200 OK
                      (< 5 segundos ⚡)
                             │
                             ▼ (background task)
                      Iterar entry[]
                             │
                             ▼
                      Iterar changes[]
                             │
                             ▼
                  ┌──────────────────────┐
                  │   ¿Qué field es?     │
                  ├──────────────────────┤
                  │  "comments"          │
                  │  "messages"          │
                  │  "mentions"          │
                  │  "stories"           │
                  └──────────────────────┘
```

---

## 🔐 Verificación de firma (HMAC SHA256)

Meta firma cada POST con tu `App Secret`. El header llega así:

```
X-Hub-Signature-256: sha256=a1b2c3d4e5f6...
```

El proceso de verificación:

```
Header recibido
      │
      ▼
Extraer algoritmo y firma
      │
      ▼
Obtener body crudo (bytes exactos)
      │
      ▼
HMAC SHA256(APP_SECRET, raw_body)
      │
      ▼
hmac.compare_digest(expected, received)
      │
  ❌ → 403     ✅ → continuar
```

> ⚠️ Se usa `hmac.compare_digest` (no `==`) para evitar ataques de timing.

---

## 🗄️ Modelo de base de datos

**Tabla:** `DataLake.webhook_logs`

| Columna       | Tipo         | Descripción                      |
| ------------- | ------------ | -------------------------------- |
| `id`          | Integer PK   | Auto-incremental                 |
| `event_type`  | String(50)   | `"comments"`, `"messages"`, etc. |
| `payload`     | JSONB        | Payload completo de Meta         |
| `received_at` | TIMESTAMP TZ | `server_default=now()`           |

---

## 📐 Estructura del payload de Instagram

Los modelos Pydantic siguen esta jerarquía (de adentro hacia afuera):

```
WebhookPayload
├── object: str               ← "instagram"
└── entry: list[Entry]
    ├── id: str
    ├── time: int
    └── changes: list[Change]
        ├── field: str        ← "comments" | "messages" | "mentions" | "stories"
        └── value: Any
```

---

## 🧱 Principios de diseño aplicados

| Principio                           | Dónde                                                                             |
| ----------------------------------- | --------------------------------------------------------------------------------- |
| **Singleton**                       | `db = Database()` y `settings = Settings()` — una sola instancia para toda la app |
| **DIP** (Inversión de dependencias) | `WebhookLogRepository` recibe `AsyncSession` inyectada, no la crea                |
| **Separación de responsabilidades** | `WebhookChecker` valida, `WebhookProcessor` procesa, `Repository` persiste        |
| **Background tasks**                | `_handle_events` corre después de responder 200 para no bloquear a Meta           |
