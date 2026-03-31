# Notes d'implémentation

- Le backend est conçu comme un noyau d'orchestration léger.
- `translate` convertit une demande libre en contrat gouverneur.
- `clarify` sert à récupérer seulement les informations manquantes.
- `governor/execute` applique des règles de gouvernance minimales et produit une réponse cadrée.
- `reformulate` convertit une sortie JSON en langage métier lisible.

Prochaines extensions possibles :
- Auth API key obligatoire
- Rate limiting
- Journalisation structurée
- SQL runtime et tables métier enrichies
- RAG documentaire
