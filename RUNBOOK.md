# Runbook de déploiement

1. Copier `.env.example` en `.env`
2. Remplir `LLM_API_KEY`
3. Optionnel : remplir `SUPABASE_URL` et `SUPABASE_SERVICE_ROLE_KEY`
4. Lancer localement : `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
5. Vérifier `/health`
6. Tester `translate -> governor/execute -> reformulate`
7. Déployer sur Render avec `uvicorn app.main:app --host 0.0.0.0 --port 10000`
