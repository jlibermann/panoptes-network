Add FITS Header to Database
===========================

This folder defines a [Google Cloud Function](https://cloud.google.com/functions/).

This function is used to add FITS header information to the meta database
(which itself is a [Cloud SQL Instanct](https://cloud.google.com/sql/docs/)).

This endpoint looks for two parameters, `headers` and `bucket_path`. If
`bucket_path` is present then the header information will be pull from the file
itself. Additionally, any `headers` will be used to update the header information
from the file. If no `bucket_path` is found then only the `headers` will be used.

> :memo: Todo: Document that explains overall structure.


Endpoint: https://us-central1-panoptes-survey.cloudfunctions.net/header-to-db

Payload: JSON message of the form:
	```json
	{
		'headers': dict,
		'bucket_path': str,
        'object_id': str,
	}
	```

Deploy
------

[Google Documentation](https://cloud.google.com/functions/docs/deploying/filesystem)

From the directory containing the cloud function. The `entry_point` is the
name of the function in `main.py` that we want called and `header-to-db`
is the name of the Cloud Function we want to create.

```bash
gcloud functions deploy \
                 header-to-db \
                 --entry-point header_to_db \
                 --runtime python37 \
                 --trigger-http
```

> :bulb: There is also a small convenience script called `deploy.sh` that
does the same thing.
```bash
./deploy.sh
```
