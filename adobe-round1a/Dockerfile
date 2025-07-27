
FROM --platform=linux/amd64 python:3.9-slim


WORKDIR /app


RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*


COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


COPY pdf_outline_extractor.py .


RUN mkdir -p /app/input /app/output


ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

CMD ["python", "pdf_outline_extractor.py"]
