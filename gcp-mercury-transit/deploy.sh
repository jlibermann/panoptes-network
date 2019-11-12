#!/bin/bash -e

echo "Deploying cloud function: mercury-transit"

gcloud functions deploy mercury-transit \
	--entry-point process_mercury_transit \
	--runtime python37 \
	--memory 1024MB \
	--trigger-http
