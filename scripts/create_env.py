"""Crée une configuration locale avec des secrets propres à la machine."""

from __future__ import annotations

import argparse
import getpass
import secrets
from pathlib import Path


def build_local_env() -> tuple[str, str]:
    admin_password = f"Asso-{secrets.token_urlsafe(12)}"
    private_password = secrets.token_hex(16)
    cloud_password = secrets.token_hex(16)
    content = "\n".join(
        [
            "APP_ENV=development",
            "DEPLOYMENT_MODE=local",
            f"JWT_SECRET={secrets.token_urlsafe(48)}",
            "JWT_ALGORITHM=HS256",
            "ACCESS_TOKEN_EXPIRE_MINUTES=30",
            "ADMIN_USERNAME=gestionnaire",
            f"ADMIN_PASSWORD={admin_password}",
            f"PRIVATE_POSTGRES_PASSWORD={private_password}",
            f"CLOUD_POSTGRES_PASSWORD={cloud_password}",
            "PRIVATE_DATABASE_URL="
            f"postgresql+psycopg://association:{private_password}"
            "@db-private:5432/association_private",
            "CLOUD_DATABASE_URL="
            f"postgresql+psycopg://association:{cloud_password}"
            "@db-cloud:5432/association_cloud",
            "AUTO_CREATE_SCHEMA=false",
            "SEED_DEMO_DATA=true",
            "",
        ]
    )
    return content, admin_password


def build_hybrid_env(cloud_url: str) -> tuple[str, str]:
    if cloud_url.startswith("postgresql://"):
        cloud_url = cloud_url.replace("postgresql://", "postgresql+psycopg://", 1)
    if not cloud_url.startswith("postgresql+psycopg://"):
        raise ValueError("L’URL doit être une URL de connexion PostgreSQL Supabase.")
    if "sslmode=" not in cloud_url:
        separator = "&" if "?" in cloud_url else "?"
        cloud_url = f"{cloud_url}{separator}sslmode=require"

    admin_password = f"Asso-{secrets.token_urlsafe(12)}"
    private_password = secrets.token_hex(16)
    content = "\n".join(
        [
            "APP_ENV=development",
            "DEPLOYMENT_MODE=hybrid",
            f"JWT_SECRET={secrets.token_urlsafe(48)}",
            "JWT_ALGORITHM=HS256",
            "ACCESS_TOKEN_EXPIRE_MINUTES=30",
            "ADMIN_USERNAME=gestionnaire",
            f"ADMIN_PASSWORD={admin_password}",
            f"PRIVATE_POSTGRES_PASSWORD={private_password}",
            "PRIVATE_DATABASE_URL="
            f"postgresql+psycopg://association:{private_password}"
            "@db-private:5432/association_private",
            f"CLOUD_DATABASE_URL={cloud_url}",
            "AUTO_CREATE_SCHEMA=false",
            "SEED_DEMO_DATA=true",
            "",
        ]
    )
    return content, admin_password


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="remplace un fichier .env existant")
    parser.add_argument("--hybrid", action="store_true", help="utilise Supabase pour les activités")
    args = parser.parse_args()

    destination = Path(".env.hybrid" if args.hybrid else ".env")
    if destination.exists() and not args.force:
        raise SystemExit(f"{destination} existe déjà. Utilisez --force pour le remplacer.")

    try:
        if args.hybrid:
            cloud_url = getpass.getpass("URL PostgreSQL Supabase (saisie masquée) : ")
            content, admin_password = build_hybrid_env(cloud_url)
        else:
            content, admin_password = build_local_env()
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    destination.write_text(content, encoding="utf-8")
    print(f"Configuration créée dans {destination}")
    print("Utilisateur : gestionnaire")
    print(f"Mot de passe local : {admin_password}")


if __name__ == "__main__":
    main()
