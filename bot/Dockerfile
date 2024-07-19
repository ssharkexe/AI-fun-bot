FROM python:3.11-alpine
WORKDIR /bot
COPY requirements.txt requirements.txt
RUN apk add gcc musl-dev libffi-dev
RUN pip install --upgrade pip && pip install -r requirements.txt && chmod 755 .
COPY . .
ENV TZ Europe/Moscow
RUN chmod -R 777 ./
# CMD ["python3", "-u", "main.py"]