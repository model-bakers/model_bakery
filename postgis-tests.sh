# Set a different port than postgres' default (in case the user is already running postgres locally)
export PGPORT=4111
export PGUSER=postgres
export PGPASSWORD=postgres
export TEST_DB=postgis

# Run the postgis container
docker run --rm --name modelbakery -e POSTGRES_HOST_AUTH_METHOD=trust -p ${PGPORT}:5432 -d postgis/postgis:11-3.0

# Wait a few seconds so the DB container can start up
echo "Waiting for DB container..."
sleep 4s

# Enable all of the extensions needed on the template1 database
docker exec modelbakery /bin/bash -c "psql template1 -c \"CREATE EXTENSION IF NOT EXISTS citext;\" -U postgres"
docker exec modelbakery /bin/bash -c "psql template1 -c \"CREATE EXTENSION IF NOT EXISTS hstore;\" -U postgres"
docker exec modelbakery /bin/bash -c "psql template1 -c \"CREATE EXTENSION IF NOT EXISTS postgis;\" -U postgres"

# Run the tests
python -m pytest

# Spin down the postgis container
docker stop modelbakery
