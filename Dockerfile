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
COPY gunicorn.conf.py .
CMD ["gunicorn", "-c", "gunicorn.conf.py", "pickpockett:app"]
