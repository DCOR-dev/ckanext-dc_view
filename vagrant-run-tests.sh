set -e
set -x
# Set CKAN_INI to testing
export CKAN_INI=/etc/ckan/default/ckan.ini
# Go to the directory of this script
cd "$(dirname "${BASH_SOURCE[0]}")"
# Source the CKAN environment
source /usr/lib/ckan/default/bin/activate
# Update pip
pip install --upgrade pip wheel
# Update all DCOR extensions
dcor update --yes
# Install the current package in editable mode for testing
pip install -e .
pip install -r ckanext/dc_view/tests/requirements.txt
# run tests with coverage
coverage run --source=ckanext.dc_view --omit=*tests* -m pytest -p no:warnings ckanext
# Get GitHub environment variables so codecov detects GH Actions (allow command to fail)
export $(grep -v '^#' environment.txt | xargs) || exit 0
curl -Os https://uploader.codecov.io/latest/linux/codecov
chmod +x codecov
./codecov
