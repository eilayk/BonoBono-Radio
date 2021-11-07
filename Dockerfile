# syntax=docker/dockerfile:1
FROM python:3.10.0-alpine3.14
RUN apk add --no-cache libffi-dev libsodium-dev opus-dev python3-dev ffmpeg gcc musl-dev make cmake
COPY requirements.txt requirements.txt
RUN pip install --upgrade pip
RUN pip3 install -r requirements.txt
COPY . .
CMD [ "python3", "-d", "bot.py"]