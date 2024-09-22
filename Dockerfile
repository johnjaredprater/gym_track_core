FROM python:3.12-slim-bookworm

WORKDIR /app
COPY . /app

RUN apt update -y && apt install libmariadb3 libmariadb-dev gcc -y

RUN pip install .

# Expose the port the app runs on
EXPOSE 80

# Run the app with the Litestar CLI
CMD ["litestar", "run", "--host", "0.0.0.0", "--port", "80"]
