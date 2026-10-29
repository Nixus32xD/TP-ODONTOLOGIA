FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements.txt requirements-lock.txt requirements-stack.txt ./
RUN pip install --no-cache-dir -r requirements-lock.txt -r requirements-stack.txt
COPY odontologia ./odontologia
COPY docker-entrypoint.sh ./
RUN chmod +x docker-entrypoint.sh && mkdir -p /data
EXPOSE 8000
CMD ["./docker-entrypoint.sh"]
