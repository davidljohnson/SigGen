FROM python:3.11.6-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5050

ENV NAME World

CMD ["python3", "app.py"]
