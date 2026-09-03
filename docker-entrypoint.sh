#!/bin/sh
set -eu

alembic -c alembic-private.ini upgrade head
alembic -c alembic-cloud.ini upgrade head

exec "$@"
