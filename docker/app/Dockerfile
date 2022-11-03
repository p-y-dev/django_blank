FROM python:3.10

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN apt-get update -y && apt-get upgrade -y

RUN apt-get install -y gdal-bin libgdal-dev
RUN apt-get install -y python3-gdal
RUN apt-get install -y binutils libproj-dev

COPY ./staticfiles ./staticfiles

COPY requirements.txt /requirements.txt

RUN pip3 install --upgrade pip
RUN pip3 install -r /requirements.txt

COPY ./src ./app

WORKDIR /app

RUN mkdir media || true
RUN mkdir static || true
RUN mkdir beat || true
RUN mkdir log || true
