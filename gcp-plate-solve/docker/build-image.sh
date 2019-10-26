#!/bin/bash -e
SOURCE_DIR="${PANDIR}/panoptes-network/gcp-plate-solve"
CLOUD_FILE="cloudbuild.yaml"

cd "${SOURCE_DIR}"

echo "Removing all __pycache__ and .pyc files before building."
find . \( -name '__pycache__' -or -name '*.pyc' \) -delete

echo "Using ${CLOUD_FILE}"
echo "Building gcp-plate-solve"
gcloud builds submit \
    --timeout="1h" \
    --config "${SOURCE_DIR}/docker/${CLOUD_FILE}" \
    "${SOURCE_DIR}"

