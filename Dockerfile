FROM python:3.11-slim

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN apt-get update && apt-get install -y default-libmysqlclient-dev gcc

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./app /code/app
# COPY ./.env /code/.env

EXPOSE 3333
CMD ["fastapi", "run", "app/main.py", "--port", "3333"]
