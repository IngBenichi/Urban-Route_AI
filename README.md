# Urban Route AI

<p align="left">
  <strong>Urban Route AI</strong> es una plataforma web para planificar rutas de bus en Barranquilla, con backend en FastAPI, frontend en Next.js, base de datos PostgreSQL y asistencia de IA para explicar trayectos de forma clara.
</p>

## Características

- Búsqueda de rutas directas y con transbordos.
- Planificación de trayectos desde una ubicación de origen hacia un destino.
- Módulo de IA para narrar la ruta y dar recomendaciones.
- Panel de administración para rutas, paraderos y autenticación.
- API REST documentada con FastAPI.
- Despliegue con Docker Compose.

## Arquitectura

- Backend: FastAPI + SQLAlchemy + Alembic.
- Frontend: Next.js 14 + React 18.
- Base de datos: PostgreSQL 16.
- Servicios auxiliares: geocodificación, motor de búsqueda, IA y limitación de tasa.

## Requisitos

- Docker y Docker Compose.
- Opcional para desarrollo local: Python 3.12 y Node.js 20.
- Variables de entorno configuradas desde el archivo `.env`.

## Configuración

1. Copia el ejemplo de entorno y ajusta los valores sensibles:

```bash
cp .env.example .env
```

2. Completa al menos estos valores:

- `JWT_SECRET`
- `ADMIN_PASSWORD`
- `GROK_API_KEY`
- `MAPTILER_API_KEY`
- `FRONTEND_URL`
- `NEXT_PUBLIC_API_URL`

## Ejecutar con Docker

Para levantar toda la solución en producción:

```bash
docker compose up --build -d
```

Servicios expuestos por defecto:

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`
- PostgreSQL: `localhost:5432`

El servicio `pgadmin` queda desactivado por defecto mediante perfil. Si lo necesitas para administración, ejecuta:

```bash
docker compose --profile tools up --build -d
```

## Ejecución local sin Docker

### Backend

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm ci
npm run dev
```

## Variables de entorno

Ejemplo de las variables más importantes:

- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_DB`
- `DATABASE_URL`
- `SYNC_DATABASE_URL`
- `JWT_SECRET`
- `JWT_ALGORITHM`
- `JWT_EXPIRE_HOURS`
- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`
- `GROK_API_KEY`
- `GROK_MODEL`
- `MAPTILER_API_KEY`
- `FRONTEND_URL`
- `NEXT_PUBLIC_API_URL`

## Endpoints principales

- `POST /api/auth/login`
- `GET /api/routes`
- `GET /api/routes/{id}`
- `POST /api/routes`
- `PUT /api/routes/{id}`
- `DELETE /api/routes/{id}`
- `GET /api/stops`
- `GET /api/stops/{id}`
- `POST /api/stops`
- `PUT /api/stops/{id}`
- `DELETE /api/stops/{id}`
- `POST /api/search`
- `POST /api/search/plan`
- `POST /api/ai/recommend`

## Estructura

```text
urban-route-ai-clone/
├── backend/
├── frontend/
├── scraper/
├── docker-compose.yml
└── README.md
```

## Notas de despliegue

- En producción, `NEXT_PUBLIC_API_URL` debe apuntar a la URL pública real de la API.
- Si despliegas detrás de un proxy inverso, puedes ajustar esa variable al dominio final.
- Los secretos deben mantenerse fuera del repositorio y cargarse desde `.env` o el entorno del servidor.

## Contribución

1. Crea una rama nueva.
2. Haz tus cambios con commits pequeños.
3. Abre un pull request con una descripción clara.

## Licencia

Este repositorio no incluye una licencia explícita todavía. Si vas a publicarlo como open source, agrega un archivo `LICENSE` con la licencia elegida.