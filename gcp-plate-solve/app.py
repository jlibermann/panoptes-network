import os
import sys
import tempfile

from flask import Flask
from flask import request
from flask import jsonify

from google.cloud import storage
import google.cloud.logging

from panoptes.utils.images import fits as fits_utils

logging_client = google.cloud.logging.Client()
logging_client.setup_logging()

app = Flask(__name__)

PROJECT_ID = os.getenv('PROJECT_ID', 'panoptes-exp')

# Storage
try:
    storage_client = storage.Client(project=PROJECT_ID)
except RuntimeError:
    print(f"Can't load Google credentials, exiting")
    sys.exit(1)

BUCKET_NAME = os.getenv('BUCKET_NAME', 'panoptes-processed-images')

OUTPUT_BUCKET_NAME = os.getenv('OUTPUT_BUCKET_NAME', 'panoptes-solved-images')


@app.route('/', methods=['GET', 'POST'])
def main():
    """Get the latest records as JSON.

    Returns:
        TYPE: Description
    """
    print(f"Plate solvingstarted")
    if request.json:
        params = request.get_json(force=True)
        bucket_path = params.get('bucket_path', None)
        if bucket_path is not None:

            solve_kwargs = params.get('solve_kwargs', dict())

            with tempfile.TemporaryDirectory() as tmp_dir_name:
                print(f'Creating temp directory {tmp_dir_name} for {bucket_path}')
                try:
                    print(f'Downloading image for {bucket_path}.')
                    local_path = download_blob(bucket_path, tmp_dir_name)
                    print(f'Plate solving {local_path}.')

                    solve_info = fits_utils.get_solve_field(local_path, **solve_kwargs)

                    solved_file = solve_info['solved_fits_file']

                    upload_blob(solved_file, bucket_path)

                    return jsonify(bucket_path=f'{OUTPUT_BUCKET_NAME}/{solved_file}',
                                   solve_info=solve_info)
                except Exception as e:
                    print(f'Problem with subtracting background: {e!r}')
                    return jsonify(error=e)
                finally:
                    print(f'Cleaning up temp directory: {tmp_dir_name} for {bucket_path}')
        else:
            return jsonify(error="No 'bucket_path' parameter given")


def download_blob(bucket_path, dir_name):
    """Downloads a blob from the bucket."""
    bucket = BUCKET_NAME

    bucket_uri = f'gs://{bucket}/{bucket_path}'
    local_path = os.path.join(dir_name, bucket_path.replace('/', '_'))

    print(f'Downloading {bucket_uri} to {local_path}')

    with open(local_path, 'wb') as f:
        storage_client.download_blob_to_file(bucket_uri, f)

    return local_path


def upload_blob(source_file_name, destination, bucket_name=OUTPUT_BUCKET_NAME):
    """Uploads a file to the bucket."""
    print('Uploading {} to {}.'.format(source_file_name, destination))

    bucket = storage_client.get_bucket(bucket_name)

    # Create blob object
    blob = bucket.blob(destination)

    # Upload file to blob
    blob.upload_from_filename(source_file_name)

    print('File {} uploaded to {}.'.format(source_file_name, destination))

    return destination


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
