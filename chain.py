import logging
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

from schemas import ExtraccionTecnica

load_dotenv()

#configuramos el logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Se usa ChatGoogleGenerativeAI en lugar de ChatOpenAI/ChatAnthropic porque no cuento con créditos pagos en esas plataformas.
# Cumple el mismo rol dentro de LCEL: es intercambiable sin toca el resto del pipeline.
llm = ChatGoogleGenerativeAI(model="gemini-3.6-flash", temperature=0)


#armamos el template
prompt = ChatPromptTemplate.from_messages([
    ("system",
     "Sos un analista técnico. Tu tarea es extraer información técnica "
     "estructurada del texto que te proporcione el usuario: tecnologías "
     "mencionadas, nivel de criticidad del problema o arquitectura, y un "
     "resumen técnico breve."),
    ("human", "{texto}")
])


#Estructuramos y validamos
structured_llm = llm.with_structured_output(ExtraccionTecnica)
resilient_llm = structured_llm.with_retry(
    stop_after_attempt=3,
    wait_exponential_jitter=True,
)

chain = prompt | resilient_llm

#funcion asincrona
async def process_text(text: str) -> ExtraccionTecnica:
    logger.info("Iniciando extracción de entidades técnicas")
    logger.info(f"Texto de entrada ({len(text)} caracteres): {text[:80]}...")

    try:
        resultado = await chain.ainvoke({"texto": text})
        logger.info("Extracción validada correctamente")
        logger.info(f"Resultado: {resultado.model_dump()}")
        return resultado

    except Exception as e:
        logger.error(f"Fallo la extracción tras los reintentos configurados: {e}")
        raise
    
    
    #para ejecutar el ejemplo
    
import asyncio

if __name__ == "__main__":
    texto_ejemplo = (
        "El sistema de pagos presenta timeouts intermitentes. La API está "
        "construida con FastAPI y se comunica con una base de datos "
        "PostgreSQL para las transacciones. Se usa Redis como capa de "
        "caché para las consultas frecuentes, pero se detectó que el pool "
        "de conexiones a PostgreSQL se agota bajo alta concurrencia, "
        "generando errores 500 en horarios pico."
    )

    resultado = asyncio.run(process_text(texto_ejemplo))
    print("\n--- Resultado final ---")
    print(resultado.model_dump_json(indent=2))