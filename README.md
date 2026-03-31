# Serava Governor Backend v1

Backend FastAPI professionnel pour piloter un gouverneur Serava orienté traduction, clarification, exécution et reformulation.

## Fonctionnalités
- API FastAPI structurée
- Routes `health`, `translate`, `clarify`, `governor/execute`, `reformulate`
- Contrats Pydantic explicites
- Intégration LLM compatible OpenAI / OpenRouter
- Audit Supabase non bloquant
- Prompts externalisés
- Dockerfile et docker-compose

## Arborescence
```text
app/
  api/routes.py
  core/settings.py
  models/contracts.py
  services/llm_client.py
  services/prompt_loader.py
  services/supabase_client.py
  services/translator_service.py
  services/governor_service.py
  main.py
prompts/
  translator.txt
  clarifier.txt
  reformulator.txt
```

## Démarrage local
```bash
cp .env.example .env
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Endpoints
- `GET /health`
- `POST /translate`
- `POST /clarify`
- `POST /governor/execute`
- `POST /reformulate`

## Déploiement Render
Start command conseillé :
```bash
uvicorn app.main:app --host 0.0.0.0 --port 10000
```

## Remarques
- Les mutations sont bloquées par défaut.
- L'audit Supabase n'empêche pas l'API de répondre si Supabase est indisponible.
- Avant exposition publique, ajoute authentification, rate limiting et journaux applicatifs.
