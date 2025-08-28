from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any, List
import os

app = FastAPI(title="Voyages scolaires – MVP API (Ultra simple)")

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in ALLOWED_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class StudentUpdate(BaseModel):
    nom: Optional[str] = None
    prenom: Optional[str] = None
    naissance: Optional[str] = None
    sexe: Optional[str] = None
    nationalite: Optional[str] = None
    doc_type: Optional[str] = None
    doc_number: Optional[str] = None
    doc_expiration: Optional[str] = None
    adresse: Optional[str] = None
    email: Optional[EmailStr] = None
    tel: Optional[str] = None
    contact_nom: Optional[str] = None
    contact_lien: Optional[str] = None
    contact_tel: Optional[str] = None
    allergies: Optional[bool] = None
    allergies_details: Optional[str] = None
    pai: Optional[bool] = None
    pai_ref: Optional[str] = None
    autorisation_parentale: Optional[bool] = None
    status: Optional[str] = None

DB: Dict[str, Dict[str, Any]] = {"trips": {}, "students": {}, "links": {}}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/api/v1/trips")
def create_trip(name: str, classe: str):
    trip_id = f"trip_{len(DB['trips'])+1}"
    DB["trips"][trip_id] = {"id": trip_id, "name": name, "classe": classe, "status": "active"}
    return DB["trips"][trip_id]

@app.get("/api/v1/trips")
def list_trips():
    return list(DB["trips"].values())

@app.post("/api/v1/trips/{trip_id}/links")
def generate_links(trip_id: str, count: int = 5):
    if trip_id not in DB["trips"]:
        raise HTTPException(404, "Trip not found")
    tokens = []
    for _ in range(count):
        token = f"tok_{trip_id}_{len(DB['links'])+1}"
        DB["links"][token] = {"trip_id": trip_id, "status": "active"}
        tokens.append({"token": token})
    return tokens

@app.get("/api/v1/trips/{trip_id}/students")
def list_students(trip_id: str):
    return [s for s in DB["students"].values() if s["trip_id"] == trip_id]

@app.post("/api/v1/links/{token}/upload")
async def upload_document(token: str, file: UploadFile = File(...)):
    if token not in DB["links"]:
        raise HTTPException(404, "Token not found")
    content = await file.read()
    return {"document_id": f"doc_{len(content)}"}

@app.post("/api/v1/links/{token}/ocr")
def run_ocr(token: str):
    if token not in DB["links"]:
        raise HTTPException(404, "Token not found")
    return {
        "nom": "DUPONT",
        "prenom": "Marie",
        "naissance": "12/03/2009",
        "nationalite": "FR",
        "doc_number": "XX123456",
        "doc_expiration": "01/05/2030"
    }

@app.post("/api/v1/links/{token}/submit")
def submit_form(token: str, payload: StudentUpdate):
    if token not in DB["links"]:
        raise HTTPException(404, "Token not found")
    trip_id = DB["links"][token]["trip_id"]
    student_id = f"stu_{len(DB['students'])+1}"
    data = payload.model_dump(exclude_unset=True)
    data.update({"id": student_id, "trip_id": trip_id, "status": data.get("status","incomplet")})
    DB["students"][student_id] = data
    return data

@app.get("/api/v1/links/{token}/status")
def link_status(token: str):
    if token not in DB["links"]:
        raise HTTPException(404, "Token not found")
    return {"status": "incomplet"}
