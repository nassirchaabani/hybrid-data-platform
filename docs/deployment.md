# Connexion à Supabase

Ce mode place seulement la base d'activités à distance. L'API et la base qui contient les
coordonnées personnelles restent sur la machine.

## Préparation

Dans Supabase, créer un projet puis récupérer l'URL du **Session pooler** sur le port 5432. Ce choix
convient à une application persistante et évite de dépendre d'une connexion IPv6 locale.

Lancer ensuite :

```powershell
python scripts/create_env.py --hybrid
```

Le script demande l'URL avec une saisie masquée, adapte le préfixe pour le pilote Psycopg et ajoute
`sslmode=require` si ce paramètre manque. Il génère les autres secrets et écrit le résultat dans
`.env.hybrid`, qui est ignoré par Git.

Documentation utile :

- [se connecter à PostgreSQL](https://supabase.com/docs/guides/database/connecting-to-postgres) ;
- [forcer les connexions SSL](https://supabase.com/docs/guides/platform/ssl-enforcement) ;
- [limites du palier gratuit](https://supabase.com/pricing).

## Lancement

```powershell
docker compose --env-file .env.hybrid -f compose.hybrid.yaml up --build -d
docker compose --env-file .env.hybrid -f compose.hybrid.yaml ps
docker compose --env-file .env.hybrid -f compose.hybrid.yaml logs api
```

Au démarrage, Alembic crée `members` dans PostgreSQL local et `participations` dans Supabase.
Après authentification, `GET /api/v1/deployment-info` doit signaler le mode `hybrid`, une base
cloud `remote` et TLS actif.

Ce dépôt ne met pas l'API en ligne. Il démontre un stockage réellement hybride tout en gardant les
données d'identité sur le poste.
