#!/bin/bash

set -e

echo "Waiting for PostgreSQL to start..."

until pg_isready -h database_game -p 5432; do
    sleep 1
done

echo "PostgreSQL is up and running!"

exec "$@"

echo "Command: $@"