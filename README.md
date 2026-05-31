# Urban Route AI

<p align="center">
  <a href="https://fastapi.tiangolo.com"><img src="https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png" alt="FastAPI" width="220"/></a>
</p>

<p align="center">
  <em>Urban Route AI — Sistema inteligente de rutas de buses (Backend: FastAPI · Frontend: Next.js · DB: PostgreSQL)</em>
</p>

[![Build Status](https://img.shields.io/badge/build-pending-lightgrey)](https://github.com/IngBenichi/Urban-Route_AI/actions)
[![Python](https://img.shields.io/badge/python-3.12-blue)](https://www.python.org)
[![Next.js](https://img.shields.io/badge/next.js-14-black)](https://nextjs.org)

## Descripción

Urban Route AI es una plataforma para planificar trayectos en transporte público (Barranquilla). Ofrece búsqueda de rutas directas y con transbordos, planificación paso a paso, y una capa de IA que genera narraciones y consejos sobre el trayecto.

Componentes principales:

- `backend/` — API REST desarrollada con FastAPI, autenticación vía JWT, acceso a PostgreSQL (SQLAlchemy async + Alembic).
- `frontend/` — Interfaz web en Next.js para usuarios y panel administrativo.
- `scraper/` — Herramientas para poblar la base de datos desde fuentes públicas.

## Características

- Búsqueda de rutas y planificación (directas y con transbordos).
- Generador de narraciones usando un motor de IA (configurable mediante `GROK_API_KEY`).
- Panel administrativo para gestionar `routes` y `stops`.
- Docker Compose para despliegue local/producción.

## Quick start (Docker)

1. Copia el fichero de entorno y ajusta valores sensibles:

```bash
cp .env.example .env
# Edita .env y cambia secretos y claves
```

2. Levanta los servicios:

```bash
docker compose up --build -d
```

3. Accede a:

- Frontend: http://localhost:3000
- Backend docs (Swagger): http://localhost:8000/docs

> Para habilitar `pgadmin` usa el perfil `tools`:

```bash
docker compose --profile tools up -d
```

## Desarrollo local (sin Docker)

Backend (recomendado Python 3.12):

```bash
cd backend
# Instalar dependencias (uv manages virtual env via uv)
uv sync
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend:

```bash
cd frontend
npm ci
npm run dev
```

## Variables importantes

Edita `.env` o exporta estas variables en tu entorno de despliegue:

- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`
- `DATABASE_URL`, `SYNC_DATABASE_URL`
- `JWT_SECRET`, `JWT_ALGORITHM`, `JWT_EXPIRE_HOURS`
- `ADMIN_USERNAME`, `ADMIN_PASSWORD`
- `GROK_API_KEY`, `GROK_MODEL`
- `MAPTILER_API_KEY`, `FRONTEND_URL`, `NEXT_PUBLIC_API_URL`

## API endpoints principales

- `POST /api/auth/login` — obtener token de administrador
- `GET /api/routes` — listar rutas
- `GET /api/routes/{id}` — detalle de ruta
- `POST /api/routes` — crear ruta (admin)
- `PUT /api/routes/{id}` — actualizar ruta (admin)
- `DELETE /api/routes/{id}` — eliminar ruta (admin)
- `GET /api/stops` — listar paraderos
- `POST /api/search` — buscar rutas
- `POST /api/search/plan` — planificar ruta con narración IA

## Contribuir

1. Fork y crea una rama para tu feature: `git checkout -b feature/my-feature`
2. Haz commits pequeños y descriptivos.
3. Abre un Pull Request con la explicación y pasos para probar.

## Licencia

Por ahora no hay licencia especificada. Si quieres publicar esto como open source, añade un archivo `LICENSE` con la licencia deseada (por ejemplo MIT).

---

Si quieres, puedo también añadir badges reales (CI, coverage) y un `LICENSE` en el repo.