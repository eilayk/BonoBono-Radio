# syntax=docker/dockerfile:1
FROM python:3.10.0-alpine3.14
RUN apk add libffi-dev
RUN apk add python3-dev
RUN apk add  --no-cache ffmpeg
RUN apk add gcc
RUN apk add musl-dev
RUN apk add --no-cache make cmake
RUN apk add opus
COPY requirements.txt requirements.txt
RUN pip install --upgrade pip
RUN pip3 install -r requirements.txt
COPY . .
CMD [ "python3", "-d", "bot.py"]