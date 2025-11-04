# ingester

Responsible from creating the DB schema and ingesting data from a given dataset.

To run:

```
uv run ingester/ingest_data.py
```

## Configuration

You can configure the DB URL via the following env variables:

- `DATABASE_URL` - the full database URL

or via:

- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_HOST`
- `POSTGRES_PORT`
- `POSTGRES_DB`

You can configure the location of the dataset CVS file via:

- `DATASET_PATH`
