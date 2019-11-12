import os
import tempfile

from flask import jsonify
from google.cloud import storage

import numpy as np
from scipy.ndimage.measurements import center_of_mass
from matplotlib import pyplot as plt
from astropy.io import fits

PROJECT_ID = os.getenv('PROJECT_ID', 'panoptes-survey')
BUCKET_NAME = os.getenv('BUCKET_NAME', 'panoptes-survey')
UPLOAD_BUCKET = os.getenv('UPLOAD_BUCKET', 'panoptes-survey')
client = storage.Client(project=PROJECT_ID)
bucket = client.get_bucket(BUCKET_NAME)


def process_mercury_transit(request):
    """Responds to any HTTP request.

    Notes:
        rawpy params: https://letmaik.github.io/rawpy/api/rawpy.Params.html
        rawpy enums: https://letmaik.github.io/rawpy/api/enums.html

    Args:
        request (flask.Request): HTTP request object.
    Returns:
        The response text or any set of values that can be turned into a
        Response object using
        `make_response <http://flask.pocoo.org/docs/1.0/api/#flask.Flask.make_response>`.
    """
    request_json = request.get_json()
    if request.args and 'cr2_file' in request.args:
        cr2_file = request.args.get('cr2_file')
    elif request_json and 'cr2_file' in request_json:
        cr2_file = request_json['cr2_file']
    else:
        return f'No file requested'

    print(f'Received mercury transit file: {cr2_file}')

    with tempfile.TemporaryDirectory() as tmp_dir_name:
        # Download the file locally
        base_dir = os.path.dirname(cr2_file)
        base_fn = os.path.basename(cr2_file)
        base_name, ext = os.path.splitext(base_fn)

        print('Getting CR2 file')
        cr2_storage_blob = bucket.get_blob(cr2_file)
        tmp_fn = os.path.join(tmp_dir_name, base_fn)
        print(f'Downloading to {tmp_fn}')
        cr2_storage_blob.download_to_filename(tmp_fn)

        jpg_fn, crop_coords = crop_image(tmp_fn)
        print(f'Thumbnail name: {jpg_fn}')
        print(f'Crop coords: {crop_coords}')

    return jsonify(success=True)


def crop_image(im0,
               padding=150,
               get_closer=False,
               save_image=True,
               back_threshold=200,
               rgb_channel=0,
               upload_fits=False,
               image_title=None,
               image_size=(12, 12),
               ):
    # Remove "background" assuming sun is saturating
    im0[im0 < back_threshold] = 0

    data = im0[..., rgb_channel]

    y, x = center_of_mass(data)
    x = int(x)
    y = int(y)

    y_min = y - padding
    y_max = y + padding
    x_min = x - padding
    x_max = x + padding

    if get_closer:
        d2 = data[y - padding:y + padding, x - padding:x + padding]

        y2, x2 = center_of_mass(d2)
        y2 = int(y2)
        x2 = int(x2)

        # Adjust the center
        y3 = y_min + y2
        x3 = x_min + x2

        x_min = x3 - padding
        x_max = x3 + padding
        y_min = y3 - padding
        y_max = y3 + padding

        # Get final cut
        im1 = np.flipud(im0)[y_max:y_max, x_min:x_max, :]
    else:
        im1 = img[y_min:y_max, x_min:x_max, :]

    if save_image:
        fig, ax = plt.subplots()
        fig.set_size_inches(*image_size)
        ax.imshow(im1)
        ax.set_title(image_title, fontsize=18)
        ax.set_axis_off()
        crop_fn = jpg_fn.replace('.jpg', '-cropped.jpg')
        fig.savefig(crop_fn, transparent=False, bbox_inches='tight', dpi=180)
        plt.close()
        return crop_fn, (y_min, y_max, x_min, x_max)

    return im1


def upload_blob(source_file_name, destination_blob_name):
    """Uploads a file to the bucket."""
    bucket = client.get_bucket(UPLOAD_BUCKET)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)

    print('File {} uploaded to {}.'.format(
        source_file_name,
        destination_blob_name))
