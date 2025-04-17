#!/bin/bash

# Fail immediately if any command fails
set -e

CKAN_CONTAINER="dcor_ckan" # CKAN container name
EXTENSION_PATH="/srv/app/src_extensions/"

# Create venv and install dependencies as a root user inside the container
docker exec -u root ${CKAN_CONTAINER} bash -c "
  cd ${EXTENSION_PATH};

  # Update dcor libraries
  dcor update --yes;

  # Install ckanext-dc_view and its test requirements
  pip install .;
  pip install -r ./ckanext/dc_view/tests/requirements.txt;

  # Change ownership so that 'ckan' user can use the virtual environment
  chown -R ckan:ckan-sys ${EXTENSION_PATH}/venv
"

# Run tests on GitHub runner where container gets permissions from.
echo "Running tests in the virtual environment..."
docker exec ${CKAN_CONTAINER} bash -c "
  cd ${EXTENSION_PATH};
  # Run coverage
  coverage run --source=ckanext.dc_view --omit=*tests* -m pytest -p no:warnings ckanext;
"

# Generate the XML report
docker exec ${CKAN_CONTAINER} bash -c "
  cd ${EXTENSION_PATH};
  coverage xml;
"

echo "Tests passed inside the container."
