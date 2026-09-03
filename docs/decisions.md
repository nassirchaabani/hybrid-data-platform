# Décisions techniques

## Deux historiques Alembic

Un historique unique faciliterait l'application accidentelle d'une table sur le mauvais serveur.
Les deux configurations rendent la frontière visible, avec deux commandes de migration au lieu
d'une.

## Fédération dans FastAPI

PostgreSQL FDW aurait couplé les serveurs. Pour ce projet, deux lectures explicites sont plus simples
à tester et permettent de garder la base privée indépendante de la base distante.

## UUID sans clé étrangère distante

La base cloud ne connaît qu'un UUID. Avant d'enregistrer une activité, l'API vérifie que l'adhérent
existe. Une version plus robuste ajouterait une tâche de réconciliation pour repérer les références
orphelines.

## Deux fichiers Compose

Le mode local peut être lancé sans compte externe. Le mode hybride sert à vérifier la séparation
physique avec Supabase. Les deux modes exécutent la même image de l'API.

## Authentification limitée

Un compte injecté par l'environnement suffit pour montrer la création et la validation d'un JWT.
Une gestion multi-utilisateur demanderait un fournisseur d'identité, des rôles et une stratégie de
rotation des clés.
