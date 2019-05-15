FROM 3.7.3-stretch

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir poetry
RUN poetry config settings.virtualenvs.create false
RUN poetry install 


CMD ["python", "server.py"]
