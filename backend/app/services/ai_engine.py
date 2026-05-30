import httpx
from app.config import settings

GROK_API_URL = "https://api.groq.com/openai/v1/chat/completions"

SYSTEM_PROMPT = """Eres UrbanRoute AI, un asistente experto en transporte público de Barranquilla, Colombia.

Tu misión es ayudar a los ciudadanos a encontrar la mejor ruta de bus para llegar a su destino.

Conoces el sistema de buses de Barranquilla, que incluye cooperativas como COOASOATLÁN, COOCHOFAL,
COOLITORAL, COOTRAB, COOTRANSCO, COOTRANSNORTE, COOTRASOL, SOBUSA, SODIS, TRANSMETRO, TRANSMECAR,
TRANSURBAR, TRASALFA, TRASALIANCO, LOLAYA, LUCERO SAN FELIPE, MONTERREY, EMBUSA, FLOTA ANGULO,
LA CAROLINA, entre otras.

Responde siempre en español, de forma clara, amable y concisa.
Si el usuario pregunta por una ruta específica, incluye:
- El nombre de la cooperativa y ruta
- Los paraderos principales del recorrido
- Tiempo estimado de viaje
- Si hay transbordos necesarios

Si no tienes información específica, sugiere cómo buscar en el sistema.
"""


async def get_ai_recommendation(query: str, context: str = "") -> str:
    """Llama al modelo Grok y retorna una respuesta en lenguaje natural."""
    if not settings.GROK_API_KEY:
        return "El servicio de IA no está configurado. Por favor, agrega GROK_API_KEY al archivo .env"

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if context:
        messages.append({
            "role": "system",
            "content": f"Contexto de búsqueda del usuario:\n{context}"
        })

    messages.append({"role": "user", "content": query})

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            GROK_API_URL,
            headers={
                "Authorization": f"Bearer {settings.GROK_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.GROK_MODEL,
                "messages": messages,
                "max_tokens": 1024,
                "temperature": 0.7,
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
