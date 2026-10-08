
import os, base64, mimetypes, uuid
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

BASE = Path(__file__).parent
UPLOADS = BASE / "uploads"
GENERATED = BASE / "generated"
UPLOADS.mkdir(exist_ok=True)
GENERATED.mkdir(exist_ok=True)

app = FastAPI(title="Mi IA Multimodal")
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
app.mount("/generated", StaticFiles(directory=GENERATED), name="generated")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")
IMAGE_MODEL = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-2")
vector_store_id = os.getenv("OPENAI_VECTOR_STORE_ID", "").strip()

ALLOWED = {
    ".pdf", ".txt", ".md", ".docx", ".csv", ".json",
    ".png", ".jpg", ".jpeg", ".webp", ".gif"
}

@app.get("/", response_class=HTMLResponse)
async def home():
    return (BASE / "templates" / "index.html").read_text(encoding="utf-8")

@app.get("/health")
async def health():
    return {"ok": True, "vector_store_configured": bool(vector_store_id)}

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED:
        raise HTTPException(400, f"Tipo de archivo no permitido: {ext}")

    safe_name = f"{uuid.uuid4().hex}{ext}"
    local_path = UPLOADS / safe_name
    data = await file.read()
    local_path.write_bytes(data)

    result = {"name": file.filename, "local_name": safe_name, "size": len(data)}

    # Documentos para RAG: si hay vector store configurado, se indexan.
    if vector_store_id and ext not in {".png",".jpg",".jpeg",".webp",".gif"}:
        try:
            with open(local_path, "rb") as f:
                uploaded = client.files.create(file=f, purpose="assistants")
            client.vector_stores.files.create_and_poll(
                vector_store_id=vector_store_id,
                file_id=uploaded.id
            )
            result["indexed"] = True
            result["file_id"] = uploaded.id
        except Exception as e:
            result["indexed"] = False
            result["warning"] = str(e)

    return result

def data_url(path: Path):
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    encoded = base64.b64encode(path.read_bytes()).decode()
    return f"data:{mime};base64,{encoded}"

@app.post("/chat")
async def chat(
    message: str = Form(""),
    image_names: str = Form(""),
):
    content = []
    if message.strip():
        content.append({"type": "input_text", "text": message.strip()})

    for name in [x.strip() for x in image_names.split(",") if x.strip()]:
        p = UPLOADS / Path(name).name
        if p.exists():
            content.append({"type": "input_image", "image_url": data_url(p)})

    if not content:
        raise HTTPException(400, "Escribe un mensaje o adjunta una imagen.")

    kwargs = {
        "model": MODEL,
        "input": [{"role": "user", "content": content}],
    }

    # RAG con File Search si se configuró un vector store.
    if vector_store_id:
        kwargs["tools"] = [{
            "type": "file_search",
            "vector_store_ids": [vector_store_id]
        }]

    response = client.responses.create(**kwargs)
    return {"answer": response.output_text}

@app.post("/generate-image")
async def generate_image(prompt: str = Form(...)):
    prompt = prompt.strip()
    if not prompt:
        raise HTTPException(400, "Escribe una descripción para la imagen.")

    result = client.images.generate(
        model=IMAGE_MODEL,
        prompt=prompt,
        size="1024x1024",
    )
    b64 = result.data[0].b64_json
    filename = f"{uuid.uuid4().hex}.png"
    path = GENERATED / filename
    path.write_bytes(base64.b64decode(b64))
    return {"url": f"/generated/{filename}"}
