# Parcours API

La documentation interactive est exposée sur `/docs` et le schéma OpenAPI sur `/openapi.json`.

1. Obtenir un jeton avec `POST /api/v1/auth/token` au format formulaire OAuth2 (`username`,
   `password`).
2. Envoyer `Authorization: Bearer <jeton>`.
3. Créer un adhérent avec `POST /api/v1/members`; ses données personnelles sont écrites dans la
   base privée.
4. Créer une activité avec `POST /api/v1/participations`; elle est écrite dans la base cloud.
5. Lire la vue assemblée via `GET /api/v1/federated/members/{id}` ou l'agrégat via
   `GET /api/v1/federated/overview`.

`GET /api/v1/routing-policy` indique la destination choisie pour chaque type de champ. `/health`
vérifie que l'API répond, tandis que `/ready` teste aussi les deux connexions PostgreSQL.
`GET /api/v1/deployment-info` indique le mode local ou hybride sans exposer les URL.

La liste des adhérents accepte `limit` (1 à 100) et `offset`. Les identifiants sont des UUID
PostgreSQL natifs. L'API renvoie notamment `401` pour un jeton absent ou expiré, `404` pour un
adhérent inconnu, `409` pour un e-mail déjà présent et `422` pour une requête invalide.
