from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional
import os, secrets, psycopg
from psycopg.rows import dict_row

# ---------- Config & CORS ----------
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app = FastAPI(title="Voyages scolaires – API (Supabase Postgres)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in ALLOWED_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def dsn_with_ssl(dsn: str) -> str:
    if "sslmode=" in dsn:
        return dsn
    sep = "&" if "?" in dsn else "?"
    return dsn + f"{sep}sslmode=require"

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL manquant. Ajoutez-le dans les variables Railway.")
DATABASE_URL = dsn_with_ssl(DATABASE_URL)

# ---------- DB helpers ----------
def get_conn():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)

def init_schema():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
            create extension if not exists pgcrypto;

            create table if not exists trips(
                id uuid primary key default gen_random_uuid(),
                name text not null,
                classe text not null,
                status text not null default 'active',
                created_at timestamptz not null default now()
            );

            create table if not exists students(
                id uuid primary key default gen_random_uuid(),
                trip_id uuid not null references trips(id) on delete cascade,
                nom text, prenom text, naissance text, sexe text, nationalite text,
                doc_type text, doc_number text, doc_expiration text,
                adresse text, email text, tel text,
                contact_nom text, contact_lien text, contact_tel text,
                allergies boolean, allergies_details text,
                pai boolean, pai_ref text,
                autorisation_parentale boolean,
                status text,
                created_at timestamptz not null default now()
            );

            create table if not exists links(
                token text primary key,
                trip_id uuid not null references trips(id) on delete cascade,
                student_id uuid null references students(id) on delete set null,
                status text not null default 'active',
                created_at timestamptz not null default now()
            );
            """)
        conn.commit()

init_schema()

# ---------- Models ----------
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

# ---------- Routes ----------
@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/api/v1/trips")
def create_trip(name: str, classe: str):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            insert into trips(name, classe) values (%s, %s)
            returning id, name, classe, status, created_at
        """, (name, classe))
        row = cur.fetchone()
        conn.commit()
        return row

@app.get("/api/v1/trips")
def list_trips():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            select id, name, classe, status, created_at
            from trips
            order by created_at desc
        """)
        return cur.fetchall()

@app.post("/api/v1/trips/{trip_id}/links")
def generate_links(trip_id: str, count: int = 5):
    with get_conn() as conn, conn.cursor() as cur:
        # validate trip exists
        cur.execute("select 1 from trips where id = %s", (trip_id,))
        if not cur.fetchone():
            raise HTTPException(404, "Trip not found")
        tokens = []
        for _ in range(count):
            token = f"tok_{secrets.token_urlsafe(10)}"
            cur.execute("""
                insert into links(token, trip_id)
                values (%s, %s) on conflict do nothing
            """, (token, trip_id))
            tokens.append({"token": token})
        conn.commit()
        return tokens

@app.get("/api/v1/trips/{trip_id}/students")
def list_students(trip_id: str):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            select id, trip_id, nom, prenom, naissance, sexe, nationalite,
                   doc_type, doc_number, doc_expiration, adresse, email, tel,
                   contact_nom, contact_lien, contact_tel,
                   allergies, allergies_details, pai, pai_ref, autorisation_parentale,
                   status, created_at
            from students
            where trip_id = %s
            order by nom nulls last, prenom nulls last, created_at desc
        """, (trip_id,))
        return cur.fetchall()

@app.post("/api/v1/links/{token}/upload")
async def upload_document(token: str, file: UploadFile = File(...)):
    # Vérifie que le token existe
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("select trip_id from links where token = %s", (token,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, "Token not found")
    content = await file.read()
    # Ici on pourrait stocker dans Supabase Storage ; pour l'instant, on renvoie un id basé sur la taille
    return {"document_id": f"doc_{len(content)}"}

@app.post("/api/v1/links/{token}/ocr")
def run_ocr(token: str):
    # Stub d’OCR : renvoie des champs d’exemple
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("select 1 from links where token = %s", (token,))
        if not cur.fetchone():
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
    data = payload.model_dump(exclude_unset=True)
    with get_conn() as conn, conn.cursor() as cur:
        # Récupère le trip lié au token
        cur.execute("select trip_id from links where token = %s", (token,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, "Token not found")
        trip_id = row["trip_id"]
        # Insère l'élève
        cols = ["trip_id"] + list(data.keys())
        vals = [trip_id] + list(data.values())
        placeholders = ", ".join(["%s"] * len(vals))
        cur.execute(f"insert into students({', '.join(cols)}) values ({placeholders}) returning *", vals)
        stu = cur.fetchone()
        # Lie le token à l'élève
        cur.execute("update links set student_id = %s where token = %s", (stu["id"], token))
        conn.commit()
        return stu

@app.get("/api/v1/links/{token}/status")
def link_status(token: str):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            select s.status
            from links l
            left join students s on s.id = l.student_id
            where l.token = %s
        """, (token,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, "Token not found")
        return {"status": row["status"] or "incomplet"}
