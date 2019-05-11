FROM 3.7.3-stretch

WORKDIR /app

COPY . /app

ENV SHELL=/bin/bash
RUN curl https://rclone.org/install.sh | sudo bash
RUN pip install poetry


CMD ["uvicorn", "server:app"]
