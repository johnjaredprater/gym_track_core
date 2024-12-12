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

Spin up the server & reload on changes with:
```
litestar run -r -d
```

Check it's working by visiting the schema endpoint: http://localhost:8000/api/docs.

To run tests, use
```
pip install -e .["test"]
```

### Database
```
docker run -e MYSQL_ROOT_PASSWORD=mypass -p 3306:3306 -d mysql:9.1.0

export GOOGLE_APPLICATION_CREDENTIALS=~/gym-tracking-firebase-key.json
```

#### Alembic

```
alembic revision --autogenerate -m "revision name"
alembic upgrade head
```
