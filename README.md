# Voyages scolaires – MVP (Flat + Postgres Supabase)

Cette version enregistre dans **Supabase Postgres** (persistant).
Toujours **4 fichiers à la racine** pour un upload facile via GitHub Web.

## Variables à définir sur Railway
- `DATABASE_URL` = l’URI Supabase (ajoutez `?sslmode=require` si besoin)
- `ALLOWED_ORIGINS` = ajoutez votre domaine Lovable et `https://*.up.railway.app`
- (option) `JWT_SECRET`

## Démarrer
- `Dockerfile` lance automatiquement : `uvicorn main:app --host 0.0.0.0 --port 8000`
- Ouvrez `…railway.app/docs` pour tester.

## Schéma créé automatiquement
- `trips` (id UUID, name, classe, status, created_at)
- `students` (id UUID, trip_id FK, …)
- `links` (token PK, trip_id FK, student_id FK NULL, status, created_at)

> NB : on utilise `gen_random_uuid()` de l’extension `pgcrypto`.
