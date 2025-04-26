# Gym Track Core

### Development

With pyenv

```bash
pyenv install 3.12.6
pyenv local 3.12.6
python -m venv .env312
source .env312/bin/activate
```

Install dependencies with:
```
pip install -e .
```

Spin up the DB with
```
docker run -e MYSQL_ROOT_PASSWORD=mypass -p 3306:3306 mysql:9.1.0
```

Pre-fill data with
```
alembic upgrade head
```


Spin up the server & reload on changes with:
```
export GOOGLE_APPLICATION_CREDENTIALS=~/gym-tracking-firebase-key.json
export ANTHROPIC_API_KEY=$(cat ~/anthropic-api-key)
litestar run -r -d
```

Check it's working by visiting the schema endpoint: http://localhost:8000/api/docs.

To run tests, use
```
pip install -e .["test"]
pytest
```

### Connect to local MySql container
```
docker exec -it <container id> mysql -u root -p
```

### Create a new Alembic migration

```
alembic revision --autogenerate -m "revision name"
alembic upgrade head
```
