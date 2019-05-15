FROM python:3.7.3-stretch

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir poetry
RUN poetry config settings.virtualenvs.create false
RUN poetry install 
RUN apt update
RUN apt install -y python3-setuptools
RUN easy_install dist/*


CMD ["python", "server.py"]
