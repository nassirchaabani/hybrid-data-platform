# Dépannage Docker Desktop sous Windows

## Le moteur Linux ne répond pas

Une erreur sur `dockerDesktopLinuxEngine/_ping` signifie généralement que Docker Desktop n'est pas
prêt. Redémarrer Docker Desktop, attendre l'état **Engine running**, puis contrôler :

```powershell
docker version
docker info
```

## `exec format error` sur PostgreSQL

Le projet utilise `postgres:16-bookworm`, plus fiable que l'image Alpine sur la configuration
Windows/WSL utilisée pendant le développement. Si l'image locale est corrompue :

```powershell
docker compose down
docker image rm postgres:16-bookworm
docker pull --platform linux/amd64 postgres:16-bookworm
docker compose up --build
```

Vérifier également que Docker Desktop utilise les conteneurs Linux.

## Conservation des données

`docker compose down` retire les conteneurs et les réseaux mais conserve les volumes. L'option
`-v` supprime aussi les deux bases et ne doit être utilisée que si leur contenu peut être perdu.
