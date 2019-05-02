FROM 3.7.3-stretch

WORKDIR /app

COPY . /app

RUN apt install lame

CMD ["python", "tagger.py"]
