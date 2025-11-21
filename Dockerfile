FROM python:2.7.18-slim
WORKDIR /app
COPY . /app
CMD ["python", "main.py"]