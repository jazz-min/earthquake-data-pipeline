#!/bin/bash

# Exit on any error
set -e

# Wait for the database to be ready
echo " Waiting for the database..."
sleep 5

# Set up Superset DB
echo " Upgrading the Superset metadata database..."
superset db upgrade

# Create admin user if not already created
echo "Creating admin user..."
superset fab create-admin \
    --username "$SUPERSET_ADMIN_USERNAME" \
    --firstname "$SUPERSET_ADMIN_FIRSTNAME" \
    --lastname "$SUPERSET_ADMIN_LASTNAME" \
    --email "$SUPERSET_ADMIN_EMAIL" \
    --password "$SUPERSET_ADMIN_PASSWORD"

# Load default roles and permissions
echo "Initializing roles and permissions..."
superset init


# Start Superset server (if using this script as entrypoint)
echo " Starting Superset server..."
sh -c "gunicorn --bind 0.0.0.0:8088 'superset.app:create_app()'"