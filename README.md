# Introduction
GlassGov, is a platform that empowers citizens to understand, discuss, and influence the policies that shape their lives. In a world where government often feels distant, GlassGov brings clarity and connection, transforming local concerns into meaningful civic insight.

By combining open legislative data with AI-powered summaries and community feedback, GlassGov helps people see how their everyday issues relate to real bills and actions in their state. It gives citizens a clear, accessible view of what’s happening in government, and how their voices can drive change.

GlassGov reimagines civic engagement for the modern age, making participation easier, transparency stronger, and democracy more collaborative.

🌐 **https://www.glassgov.tech/**

<img width="1050" height="512" alt="image" src="https://github.com/user-attachments/assets/17b6f0f8-1231-4fb0-9c60-7e2c73ad506f" />

# Team
Made by:

**David Kan**: University of Georgia (3rd year) B.S Computer Science 
**Jasmine Nguyen**: University of Georgia (3rd year) B.S Data Science 


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

