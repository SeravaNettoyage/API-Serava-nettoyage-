# Serava Governor Backend v1

Backend FastAPI minimal et professionnel pour communiquer avec le gouverneur Serava.

## Ce que contient ce pack
- API FastAPI prête à lancer
- Contrats JSON/Pydantic pour les requêtes gouverneur
- Routes principales : `health`, `translate`, `clarify`, `governor/execute`, `reformulate`
- Intégration Supabase via variables d'environnement
- Intégration LLM via API compatible OpenAI
- Prompts système séparés : traducteur, clarificateur, reformulateur
- SQL runtime pour audit et journalisation
- Exemples de requêtes
- Dockerfile et `docker-compose.yml`

## Architecture
Utilisateur/outil -> `/translate` -> JSON gouverneur -> `/governor/execute` -> sortie gouverneur -> `/reformulate`

## Démarrage rapide
1. Copier `.env.example` en `.env`
2. Renseigner les variables Supabase et LLM
3. Installer les dépendances :
   ```bash
   pip install -r requirements.txt
   ```
4. Lancer l'API :
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
5. Ouvrir :
   - Swagger UI: `http://localhost:8000/docs`
   - Healthcheck: `http://localhost:8000/health`

## Variables importantes
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `LLM_BASE_URL`
- `LLM_API_KEY`
- `LLM_MODEL_TRANSLATE`
- `LLM_MODEL_CLARIFY`
- `LLM_MODEL_REFORMULATE`
- `ALLOW_GOVERNOR_MUTATIONS`

## Flux recommandé
1. Envoyer une demande libre à `/translate`
2. Si `needs_clarification=true`, envoyer à `/clarify`
3. Quand le JSON est prêt, envoyer à `/governor/execute`
4. Reformuler la sortie si besoin via `/reformulate`

## Important
- Ce pack n'invente pas la doctrine métier.
- Les modifications sont bloquées par défaut (`ALLOW_GOVERNOR_MUTATIONS=false`).
- Le backend est prêt pour un usage interne. Il faut ajouter auth/rate limiting avant exposition publique.
