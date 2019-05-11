FROM 3.7.3-stretch

WORKDIR /app

COPY . /app

ENV SHELL=/bin/bash
RUN curl https://rclone.org/install.sh | sudo bash
RUN pip install poetry
RUN poetry install 
RUN sh scripts/update_rclone_config.sh



CMD ["uvicorn", "server:app"]
