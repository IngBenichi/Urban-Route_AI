FROM python:3.12-slim

# Instalar uv via pip (evita depender de ghcr.io)
RUN pip install uv --no-cache-dir

WORKDIR /app

# Instalar dependencias (layer cacheado)
COPY pyproject.toml ./
RUN uv sync --no-dev

# Copiar código fuente
COPY . .

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
