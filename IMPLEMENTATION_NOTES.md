# Notes d'implémentation (v1.1)

Ce backend a évolué vers une architecture d'orchestration plus robuste intégrant un moteur de connaissance documentaire (RAG).

## Architecture du Moteur Documentaire

### 1. Ingestion & Chunking (`BookIngestionService`)
- Les PDF sont lus via `pypdf`.
- Le texte est découpé en segments (chunks) par `ChunkingService` selon les paramètres `CHUNK_MAX_CHARS` et `CHUNK_OVERLAP_CHARS`.
- Chaque chunk est stocké dans la table `book_chunks` de Supabase avec son index et ses métadonnées.

### 2. Extraction de Connaissances (`KnowledgeExtractionService`)
- Pour chaque chunk, un appel au LLM (`LLM_MODEL_EXTRACT`) est effectué avec le prompt `extract_rules`.
- Les faits métiers (surfaces, fibres, taches, produits, risques, etc.) sont extraits de manière structurée et stockés dans `knowledge_rules`.

### 3. Recherche (Retrieval) MVP (`RetrievalService`)
- La recherche actuelle est une recherche textuelle par mots-clés (`ILike`).
- Les termes de la requête sont normalisés et comparés au contenu des chunks et des règles.
- Un score simple est calculé en fonction du nombre d'occurrences pour classer les résultats.

### 4. Gouverneur avec RAG (`GovernorService`)
- Si un `book_id` est présent dans le `context` ou les `entities` de la requête, le service déclenche une recherche documentaire.
- Le contexte récupéré (chunks + règles) est injecté dans le prompt `governor_knowledge` envoyé au LLM (`LLM_MODEL_GOVERNOR`).
- En cas d'échec de la recherche ou d'absence de livre, un fallback génère une réponse conservatrice sans connaissance documentaire.

## Stratégie de Persistance
- **Supabase** est utilisé comme base de données principale.
- Les schémas sont définis dans `sql/knowledge_engine.sql`.
- L'audit des requêtes et réponses est conservé dans `governor_audit`.

## Évolutions futures
- **Recherche Sémantique** : Le schéma SQL contient déjà une colonne `embedding`. L'étape suivante consiste à intégrer un service d'embeddings (ex: OpenAI `text-embedding-3-small`) et à utiliser `pgvector` pour la recherche de similarité.
- **Gestion des Permissions** : Ajouter des rôles et des permissions par livre ou par organisation.
- **Cache de Connaissance** : Mettre en cache les résultats de recherche fréquents pour réduire la latence et les coûts LLM.
