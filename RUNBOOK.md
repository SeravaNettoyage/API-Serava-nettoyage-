# Runbook de démarrage et test (v1.1)

Ce guide détaille les étapes pour lancer et tester localement le backend Serava avec son moteur documentaire.

## 1. Préparation de l'environnement
1. Copier `.env.example` en `.env` : `cp .env.example .env`
2. Configurer les clés API :
   - `INTERNAL_API_KEY` : Clé pour authentifier vos requêtes (`X-API-Key`).
   - `LLM_API_KEY` : Votre clé API OpenAI ou OpenRouter.
   - `SUPABASE_URL` & `SUPABASE_SERVICE_ROLE_KEY` : Pour l'audit et le moteur documentaire.
3. Installer les dépendances : `pip install -r requirements.txt`

## 2. Lancement local
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 3. Flux de test complet

### A. Vérification de santé
```bash
curl http://localhost:8000/health
```

### B. Ingestion documentaire (RAG)
1. **Upload d'un PDF** :
   Utilisez un client comme Postman ou `curl` pour uploader un PDF sur `POST /books/upload`.
   *Récupérez le `book_id` retourné.*

2. **Extraction de connaissances** :
   ```bash
   curl -X POST http://localhost:8000/books/{book_id}/extract \
     -H "X-API-Key: votre_cle"
   ```

3. **Recherche documentaire** :
   ```bash
   curl -X POST http://localhost:8000/knowledge/search \
     -H "X-API-Key: votre_cle" \
     -H "Content-Type: application/json" \
     -d '{"book_id": "{book_id}", "query": "nettoyage marbre"}'
   ```

### C. Gouverneur avec connaissance
Testez l'exécution en passant le `book_id` dans le contexte :
```bash
curl -X POST http://localhost:8000/governor/execute \
  -H "X-API-Key: votre_cle" \
  -H "Content-Type: application/json" \
  -d '{
    "request_type": "operational_recommendation",
    "source_text": "Comment nettoyer une tache de vin sur du marbre ?",
    "context": {"book_id": "{book_id}"}
  }'
```

## 4. Déploiement
Le backend est prêt à être déployé sur Render avec la commande :
`uvicorn app.main:app --host 0.0.0.0 --port 10000`
*(Assurez-vous de configurer toutes les variables d'environnement dans le dashboard Render).*
