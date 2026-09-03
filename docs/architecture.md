# Notes d'architecture

## Pourquoi deux bases ?

Le cas étudié sépare les données selon leur usage. Les informations qui permettent de contacter une
personne restent dans la base privée. Les données utilisées pour calculer l'activité d'un programme
peuvent être stockées dans la base cloud, mais elles ne contiennent que l'identifiant technique de
l'adhérent.

```text
                           +--> PostgreSQL privé : members
Client --> JWT --> FastAPI |
                           +--> PostgreSQL cloud : participations
```

Les modèles SQLAlchemy n'utilisent pas la même classe de base. Chaque historique Alembic ne charge
que les métadonnées de son moteur. Le test `test_data_is_physically_routed` vérifie cette
séparation.

## Requête fédérée

Une jointure SQL classique n'est pas possible puisque les tables sont dans deux serveurs différents.
Le service commence par lire l'adhérent dans la base privée, puis cherche ses participations dans la
base cloud. FastAPI assemble les deux résultats avant de répondre au client.

Cette solution est suffisante pour le volume du prototype. Les listes sont paginées, mais sur un
volume important il faudrait aussi préparer les agrégats ou utiliser un traitement asynchrone.

## Sécurité retenue

- Les routes métier demandent un JWT valable.
- La durée du jeton est de 30 minutes par défaut.
- Les secrets proviennent des variables d'environnement.
- Les bases restent sur deux réseaux Docker internes.
- Seule l'API rejoint le réseau frontal qui publie le port 8000.
- L'URL Supabase utilise TLS en mode hybride.

Le compte local n'est pas un système complet de gestion des utilisateurs. C'est une limite volontaire
du prototype.

## Cohérence

Il n'y a pas de transaction distribuée entre les deux PostgreSQL. Une participation est enregistrée
séparément, après vérification de l'existence de l'adhérent dans la base privée. Ce choix évite
d'ajouter un mécanisme complexe pour un cas d'étude de petite taille.

## Deux modes d'exécution

`compose.yaml` lance les deux PostgreSQL en local pour que le projet reste reproductible.
`compose.hybrid.yaml` conserve uniquement la base privée en local et se connecte à Supabase pour
les activités. Le code applicatif est identique dans les deux cas.
