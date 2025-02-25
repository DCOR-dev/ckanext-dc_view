#!/bin/bash

# Fail immediately if any command fails
set -e

EXTENSION_NAME="ckanext-dcor_view"  # Change this to your extension's name
CKAN_CONTAINER="${EXTENSION_NAME}-dcor-test-1" # CKAN container name
EXTENSION_PATH="/srv/app/src_extensions/"

# Create venv and install dependencies as a root user inside the container
docker exec -u root ${CKAN_CONTAINER} bash -c "
  cd ${EXTENSION_PATH};

  # Create a venv with systme site packages
  python3 -m venv --system-site-packages venv;
  source venv/bin/activate;
  pip install --upgrade pip wheel;

  # Update dcor libraries
  dcor update --yes;

  # Install ckanext-dcor_theme and its test requirements
  pip install .;
  pip install -r ./ckanext/dcor_view/tests/requirements.txt;

  # Change ownership so that 'ckan' user can use the virtual environment
  chown -R ckan:ckan-sys ${EXTENSION_PATH}/venv
"

# Run tests on GitHub runner where container gets permissions from.
echo "Running tests in the virtual environment..."
docker exec ${CKAN_CONTAINER} bash -c "
  cd ${EXTENSION_PATH};
  source venv/bin/activate;

  # Run coverage
  coverage run --source=ckanext.dcor_view --omit=*tests* -m pytest -p no:warnings ckanext;
  
  # Generate the XML report
  coverage xml
"

echo "Tests completed!"
