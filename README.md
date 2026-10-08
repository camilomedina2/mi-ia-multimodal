
# Mi IA Multimodal

Aplicación web tipo ChatGPT con:
- Chat con modelo de IA
- Subida de documentos
- Análisis de imágenes
- RAG mediante File Search
- Generación de imágenes
- Interfaz moderna

## 1. Instalar Python
Usa Python 3.10 o superior.

## 2. Instalar dependencias

Windows:
```bash
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

macOS/Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 3. Configurar la API Key

Copia `.env.example` como `.env` y coloca tu clave:

```env
OPENAI_API_KEY=tu_clave
```

No publiques el archivo `.env`.

## 4. Ejecutar

```bash
uvicorn app:app --reload
```

Abre:
http://127.0.0.1:8000

## RAG

Para usar búsqueda sobre documentos:
1. Crea un vector store en tu cuenta de API.
2. Coloca su ID en `OPENAI_VECTOR_STORE_ID`.
3. Sube PDF, DOCX, TXT, MD, CSV o JSON desde la interfaz.
4. La aplicación intentará indexarlos automáticamente.

## Imágenes

Puedes adjuntar PNG/JPG/WEBP/GIF para que la IA las analice.

También puedes escribir:
"crea una imagen de un aula moderna con estudiantes trabajando en equipo"
y pulsar "Crear imagen".

## Nota

Las llamadas a la API pueden generar costos según el modelo, almacenamiento y herramientas utilizadas.
