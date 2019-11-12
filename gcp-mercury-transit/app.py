import os
import tempfile

from flask import Flask
from flask import request
from flask import jsonify

from google.cloud import storage
import google.cloud.logging

from panoptes.utils.serializers import to_json

PROJECT_ID = os.getenv('PROJECT_ID', 'panoptes-survey')
BUCKET_NAME = os.getenv('BUCKET_NAME', 'panoptes-survey')
PRETTY_BUCKET = os.getenv('PRETTY_BUCKET', 'panoptes-pretty-pictures')
UPLOAD_BUCKET = os.getenv('UPLOAD_BUCKET', 'panoptes-survey')
# Storage
try:
    storage_client = storage.Client(project=PROJECT_ID)
except RuntimeError:
    print(f"Can't load Google credentials, exiting")
    bucket = None

logging_client = google.cloud.logging.Client()
logging_client.setup_logging()

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def main():
    """Get the latest records as JSON.

    Returns:
        TYPE: Description
    """
    print(f"Mercury transit processing")
    if request.json:
        params = request.get_json(force=True)
        cr2_file = params.get('cr2_file', None)
        if cr2_file is not None:

            with tempfile.TemporaryDirectory() as tmp_dir_name:
                print(f'Creating temp directory {tmp_dir_name} for {cr2_file}')
                try:
                    new_image_info = process_mercury_transit(cr2_file, tmp_dir_name)

                    return jsonify(**new_image_info)
                except Exception as e:
                    print(f'Problem with processing transit: {e!r}')
                    return jsonify(error=e)
                finally:
                    print(f'Cleaning up temp directory: {tmp_dir_name} for {cr2_file}')
        else:
            return jsonify(error="No 'bucket_path' parameter given")


def process_mercury_transit(cr2_file, tmp_dir_name):
    """"""

    print(f'Received mercury transit file: {cr2_file}')

    base_url = f'https://storage.googleapis.com/{BUCKET_NAME}'

    unit_id, cam_id, img_time = os.path.basename(cr2_file).split('-')
    img_time = img_time.replace('.cr2', '')

    cr2_url = f'{base_url}/{cr2_file}'
    jpg_cropped_url = cr2_url.replace('.cr2', '-cropped.jpg')
    fits_url = cr2_url.replace(BUCKET_NAME, PRETTY_BUCKET).replace('.cr2', '_g.fits')

    transit_info = {
        'unit_id': unit_id,
        'cam_id': cam_id,
        'cr2_file': cr2_url,
        'jpg_cropped_file': jpg_cropped_url,
        'fits_file': fits_url,
    }

    transit_info_fn = f'{unit_id}.json'
    transit_info_path = os.path.join(tmp_dir_name, transit_info_fn)
    with open(transit_info_path, 'w') as f:
        f.write(to_json(transit_info))
    upload_blob(transit_info_path, f'static/{unit_id}.json', bucket_name='www.panoptes-data.net')

    html = f"""
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta http-equiv="refresh" content="30">
    <title>{unit_id} {cam_id} {img_time}</title>
  </head>
  <body>
    <a href="{fits_url}">FITS</a><br />
    <img src="{jpg_cropped_url}" width="900"></img>
  </body>
</html>
    """
    html_path = os.path.join(tmp_dir_name, transit_info_fn.replace('.json', '.html'))
    with open(html_path, 'w') as f:
        f.write(html)
    upload_blob(html_path, f'{unit_id}-{cam_id}.html', bucket_name='www.panoptes-data.net')

    return transit_info


def upload_blob(source_file_name, destination_blob_name, bucket_name=BUCKET_NAME):
    """Uploads a file to the bucket."""
    bucket = storage_client.get_bucket(bucket_name)

    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)
    blob.make_public()
    blob.cache_control = 'no-cache, max-age=0'
    blob.update()

    print('File {} uploaded to {}.'.format(
        source_file_name,
        destination_blob_name))

    return blob.public_url


def download_blob(bucket_path, dir_name, use_legacy=False):
    """Downloads a blob from the bucket."""

    bucket_uri = f'gs://{bucket}/{bucket_path}'
    local_path = os.path.join(dir_name, bucket_path.replace('/', '_'))

    print(f'Downloading {bucket_uri} to {local_path}')

    with open(local_path, 'wb') as f:
        storage_client.download_blob_to_file(bucket_uri, f)

    return local_path


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
