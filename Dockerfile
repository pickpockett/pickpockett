FROM python:3.12-slim

ENV PIP_NO_CACHE_DIR 1
ENV PIP_ROOT_USER_ACTION ignore
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

EXPOSE 9119
VOLUME /data
ENV DATA_DIR=/data
ENV TZ=UTC
WORKDIR /app

COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY migrations migrations
COPY pickpockett pickpockett
CMD [ "python3", "-m" , "pickpockett"]
