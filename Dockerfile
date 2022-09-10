FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

EXPOSE 9119
VOLUME /data
ENV DATA_DIR=/data
ENV TZ=UTC
WORKDIR /app

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY migrations migrations
COPY pickpockett pickpockett
CMD [ "python3", "-m" , "pickpockett"]
