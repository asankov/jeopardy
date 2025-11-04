# joepardy

## How to run

Prerequisites:

- [Install Docker Compose](https://docs.docker.com/compose/install)
- Download the [dataset from Github](https://github.com/russmatney/go-jeopardy/blob/master/JEOPARDY_CSV.csv)
  - you can do this by running `curl -L -o dataset.csv https://raw.githubusercontent.com/russmatney/go-jeopardy/master/JEOPARDY_CSV.csv`
- Create an OpenAI Account and get an API key from [here](https://platform.openai.com/settings/organization/api-keys)
- Create `.env` file from `.env.example` and populate with your OpenAI API key

To run the project, you just need to run

```shell
docker compose up
```

or

```shell
docker-compose up # for older versions of Docker CLI
```

at the root of the project.

This will do a few things:

1. Start an empty PostgreSQL container
2. Run the `ingester` and ingest the data from the dataset into the newly created PostgreSQL database.
3. After the ingestor is done, it will start the `api` container

Docker will automatically build the container images using the Dockerfiles in their respective folders.
You do not need to build any images manually or configure access to a private registry to get them.

Once started, you can call the API on <http://localhost:8000>.
There is no UI yet, so the easiest way to interact with it is via the Swagger docs at <http://localhost:8000/docs>.

## Components

### ingester

Responsible from creating the DB schema and ingesting data from a given dataset.

### db

Contains the db models.

### api

Responsible for serving the API for the game.

### ai

Responsible for communicating with the AI model.
