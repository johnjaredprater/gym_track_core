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
