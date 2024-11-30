import uvicorn
from bson import ObjectId
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from pymongo import MongoClient
import gridfs
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import StreamingResponse
from urllib.parse import quote_plus

app = FastAPI()

MONGO_URI = "mongodb://{}:{}@{}:{}/admin".format(
    quote_plus("admin"),
    quote_plus("CapybaraLoco323%"),
    "129.146.111.32",
    "27017"
)

client = MongoClient(MONGO_URI)
db = client["archivos"]
fs = gridfs.GridFS(db)

# Configuración CORS para aceptar solicitudes de cualquier origen
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ipDocker = "http://129.146.111.32:3000/"


# Crearemos un metodo para listar todos los archivos que tenemos en la base de datos
@app.get("/")
async def list_files():
    try:
        files = fs.find()
        files_list = []
        for file in files:
            files_list.append({
                "file_id": str(file._id),
                "nombre": file.nombre,
                "tipo": file.tipo,
                "enlace": ipDocker + str(file._id)
            })
        return JSONResponse(content=files_list, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/")
async def create_upload_file(file: UploadFile = File(...)):
    try:
        filename = file.filename
        content_type = file.content_type
        file_id = fs.put(file.file, nombre=filename, tipo=content_type)
        return JSONResponse(content={"enlace": ipDocker + str(file_id)}, status_code=201)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/{file_id}")
async def read_download_file(file_id: str):
    try:
        file_cursor = fs.find_one({"_id": ObjectId(file_id)})
        if file_cursor is None:
            raise HTTPException(status_code=404, detail="File not found")
        file = fs.get(file_cursor._id)
        return StreamingResponse(file, media_type=file.tipo)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/info/{file_id}")
async def read_info_file(file_id: str):
    try:
        file_cursor = fs.find_one({"_id": ObjectId(file_id)})
        if file_cursor is None:
            raise HTTPException(status_code=404, detail="File not found")
        file = fs.get(file_cursor._id)
        return JSONResponse(content={
            "file_id": str(file_id),
            "nombre": file.nombre,
            "tipo": file.tipo,
            "enlace": ipDocker + str(file_id)
        }, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/{file_id}")
async def update_file(file_id: str, file: UploadFile = File(...)):
    try:
        file_cursor = fs.find_one({"_id": ObjectId(file_id)})
        if file_cursor is None:
            raise HTTPException(status_code=404, detail="File not found")
        fs.delete(file_cursor._id)
        filename = file.filename
        content_type = file.content_type
        file_id = fs.put(file.file, nombre=filename, tipo=content_type)
        return JSONResponse(content={"file_id": str(file_id)}, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/{file_id}")
async def delete_file(file_id: str):
    try:
        file_cursor = fs.find_one({"_id": ObjectId(file_id)})
        if file_cursor is None:
            raise HTTPException(status_code=404, detail="File not found")
        fs.delete(file_cursor._id)
        return JSONResponse(content={"message": "File deleted successfully"}, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=3000, reload=True)
