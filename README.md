# Serava Governor Backend v1.1

Backend FastAPI professionnel pour piloter un gouverneur Serava avec moteur de connaissance documentaire (RAG) intégré.

## Fonctionnalités
- API FastAPI structurée avec documentation OpenAPI (Swagger)
- **Moteur Documentaire (RAG MVP)** :
  - Ingestion de PDF avec découpage intelligent (chunking)
  - Extraction de connaissances structurées via LLM
  - Recherche par mots-clés dans les documents et règles extraites
- **Gouverneur Intelligent** :
  - Exécution de décisions basée sur le contexte documentaire (si `book_id` fourni)
  - Fallback robuste en cas d'absence de base documentaire
- **Services Métier** :
  - `translate` : Traduction de demande libre en contrat gouverneur
  - `clarify` : Gestion des informations manquantes
  - `reformulate` : Conversion de JSON en langage naturel métier
- **Infrastructure** :
  - Audit non bloquant via Supabase
  - Prompts externalisés pour une maintenance facile
  - Prêt pour Docker et déploiement cloud

## Arborescence
```text
app/
  api/
    routes.py        # Routes principales (governor, translate...)
    routes_books.py  # Routes documentaires (upload, search...)
  core/
    settings.py      # Configuration centralisée (Pydantic Settings)
  models/
    contracts.py     # Modèles Pydantic (DTOs)
  services/
    llm_client.py    # Client HTTP pour LLM
    supabase_client.py # Client Supabase (Audit + Knowledge)
    governor_service.py # Logique du gouverneur avec RAG
    book_ingestion_service.py # Ingestion PDF
    chunking_service.py # Découpage de texte
    knowledge_extraction_service.py # Extraction de règles
    retrieval_service.py # Recherche documentaire
    translator_service.py # Traduction et clarification
  main.py            # Point d'entrée FastAPI
prompts/             # Prompts LLM externalisés
sql/                 # Schémas de base de données
```

## Démarrage local
```bash
cp .env.example .env
# Remplir les clés API dans .env
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Endpoints Principaux
- `GET /health` : État de santé et configuration
- `POST /translate` : Traduction en contrat
- `POST /governor/execute` : Exécution (ajoutez `book_id` dans `context` pour le RAG)
- `POST /books/upload` : Ingestion de PDF
- `POST /books/{book_id}/extract` : Extraction des règles de connaissance
- `POST /knowledge/search` : Recherche dans la base

## Configuration (Variables clés)
- `LLM_MODEL_EXTRACT` & `LLM_MODEL_GOVERNOR` : Modèles pour le moteur documentaire.
- `CHUNK_MAX_CHARS` : Taille des segments de texte.
- `RETRIEVAL_DEFAULT_TOP_K` : Nombre de résultats de recherche.

## Remarques Techniques
- **RAG MVP** : La recherche actuelle est basée sur les mots-clés (ILike). Le champ `embedding` dans SQL est prêt pour une future extension sémantique.
- **Robustesse** : Le gouverneur dispose d'un fallback automatique si la recherche documentaire échoue ou si aucun livre n'est rattaché.
- **Sécurité** : Une clé API (`X-API-Key`) est requise pour tous les endpoints sensibles.
