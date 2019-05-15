FROM python:3.7.3-stretch

WORKDIR /app

COPY . /app

RUN apt update
RUN apt install -y libavcodec-dev libavformat-dev jq curl ffmpeg gstreamer1.0 python-gi cmake git
RUN git clone https://github.com/acoustid/chromaprint
RUN cd chromaprint && cmake -DCMAKE_BUILD_TYPE=Release -DBUILD_TOOLS=ON . && make && make install
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir poetry
RUN poetry config settings.virtualenvs.create false
RUN poetry install 
RUN unzip dist/*
RUN cd pyacoustid && python setup.py install

CMD ["python", "server.py"]
