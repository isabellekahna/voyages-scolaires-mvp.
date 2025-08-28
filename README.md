# Voyages scolaires – MVP (Ultra simple)

Ce starter tient en **4 fichiers** (pas de dossiers), pour un upload facile via GitHub Web.

## Fichiers
- `Dockerfile`
- `requirements.txt`
- `main.py` (FastAPI minimal)
- `README.md` (ce fichier)

## Déployer sur Railway (Deploy from GitHub)
1) Créez un dépôt GitHub vide (New repository).
2) **Upload files** → glissez **ces 4 fichiers** à la racine (pas de dossier).
3) Sur Railway → New Project → **Deploy from GitHub** → choisissez ce dépôt.
4) Ajoutez les Variables :
   - `JWT_SECRET` = une longue chaîne aléatoire
   - `ALLOWED_ORIGINS` = `https://*.retool.com`
   - (Optionnel pour l’instant) `DATABASE_URL` et `OCR_DEBUG` (l’app démarre sans).

Une fois déployé, ouvrez l’URL et ajoutez `/docs` pour tester.
