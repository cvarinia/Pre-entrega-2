# Pipeline de Extracción de Entidades Técnicas

Pipeline asíncrono construido con **LangChain / LCEL** que recibe un párrafo de texto sin procesar (por ejemplo, un log de error o la descripción de una arquitectura de software) y devuelve un objeto validado con las tecnologías mencionadas, el nivel de criticidad del problema y un resumen técnico.

El pipeline combina:

- **LCEL** (`prompt | model.with_structured_output(Schema)`) para componer el flujo de forma declarativa.
- **Pydantic** para forzar y validar la estructura de la salida (incluyendo una validación semántica custom).
- **`.with_retry()`** para dar resiliencia ante respuestas mal formadas o incompletas del modelo.
- **Logging** para observar el proceso de validación y los reintentos.

## Estructura del repositorio

```
.
├── schemas.py       # Modelo Pydantic (contrato de datos de salida)
├── chain.py         # Prompt, cadena LCEL, función process_text() y script de prueba
├── .env             # Variables de entorno (NO se sube al repo)
├── .gitignore
└── README.md
```

## Instalación

1. Cloná el repositorio y entrá a la carpeta del proyecto.
2. Instalá las dependencias:

   ```bash
   pip install langchain langchain-google-genai python-dotenv pydantic
   ```

3. Creá un archivo `.env` en la raíz del proyecto con tu API key:

   ```
   GOOGLE_API_KEY=tu_key_aca
   ```

   > **Nota de diseño:** el pipeline usa `ChatGoogleGenerativeAI` (Gemini) en lugar de `ChatOpenAI` / `ChatAnthropic` por disponibilidad de créditos gratuitos. La arquitectura es intercambiable: al estar basada en la interfaz `Runnable` de LangChain, cambiar de proveedor solo implica cambiar la instancia del modelo en `chain.py`, sin tocar el resto del pipeline (prompt, schema, lógica de reintentos).

## Cómo ejecutarlo

```bash
python chain.py
```

Esto corre el mini-script de prueba incluido al final de `chain.py`, que procesa un texto de ejemplo y muestra en consola:

- Los logs del proceso (inicio de extracción, texto recibido, resultado validado o error).
- El objeto final validado, en formato JSON.

## Ejemplo de salida esperada

Dado un texto de entrada como:

> "El sistema de pagos presenta timeouts intermitentes. La API está construida con FastAPI y se comunica con una base de datos PostgreSQL para las transacciones. Se usa Redis como capa de caché para las consultas frecuentes, pero se detectó que el pool de conexiones a PostgreSQL se agota bajo alta concurrencia, generando errores 500 en horarios pico."

El pipeline devuelve:

```json
{
  "tecnologias": ["FastAPI", "Redis", "PostgreSQL"],
  "nivel_de_criticidad": "alta",
  "resumen_tecnico": "API con caché en Redis y persistencia en PostgreSQL; cuello de botella en conexiones concurrentes."
}
```

## Validaciones implementadas

| Tipo de validación | Dónde ocurre | Detalle |
|---|---|---|
| Estructural | `.with_structured_output(Schema)` | Fuerza que estén presentes los 3 campos definidos en el schema. |
| Sintáctica | `.with_structured_output(Schema)` | Fuerza que la salida sea un JSON parseable. |
| De tipos | Pydantic (`ExtraccionTecnica`) | `tecnologias` debe ser lista de strings, `nivel_de_criticidad` debe ser uno de los valores del enum, `resumen_tecnico` debe ser string. |
| Semántica | `@field_validator` en `schemas.py` | La lista de `tecnologias` no puede estar vacía. |

## Resiliencia

La cadena está envuelta con `.with_retry(stop_after_attempt=3, wait_exponential_jitter=True)`: si el modelo devuelve un JSON mal formado, incompleto, o que no pasa la validación de Pydantic, se reintenta automáticamente hasta 3 veces, con un tiempo de espera creciente entre intentos (backoff exponencial con jitter) para no saturar al proveedor del modelo.
