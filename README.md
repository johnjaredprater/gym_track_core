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
litestar run -r
```

To run tests, use
```
pip install -e .["test"]
```
