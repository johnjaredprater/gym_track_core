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

To run tests, use
```
pip install -e .["test"]
```