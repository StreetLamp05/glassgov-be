# GlassGov Flask Backend (Flask + PostgreSQL)
GlassGov Backend using SQLAlchemy, Alembic (Flask-migrate), CORS, and a wsgi endpoint. 
Runs in a docker container w/ postgres.

### quick start

``` shell
git clone https://github.com/StreetLamp05/flask-skeleton.git
cd flask-skeleton
```

``` shell
cp .env.example .env
```

set up .env

```shell
docker compose up --build -d
```

``` shell
# init migrations (do once)
docker compose exec app poetry run flask db init
docker compose exec app poetry run flask db migrate -m "init"
docker compose exec app poetry run flask db upgrade
```

``` shell
# test
curl http://localhost:5001/api/v1/health
```


### important info:
#### Runtime Envs:
Dev (default): entrypoint.sh waits for Postgres, runs flask db upgrade, then starts the Flask dev server on :5000 with --debug.
For prod: switch to Gunicorn in the entrypoint.sh

## Alembic Commands
#### create a new migration (after model changes)
docker compose exec app poetry run flask db migrate -m "add movies table"

#### apply latest migrations
docker compose exec app poetry run flask db upgrade

#### show current DB head
docker compose exec app poetry run flask db current

don't run flask db init if migrations/ dir exists

