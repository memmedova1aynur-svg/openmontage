# Montaj paneli — server image
FROM python:3.13-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
      ffmpeg fonts-dejavu-core libegl1 libgles2 ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY montaj/requirements.txt /app/montaj/requirements.txt
RUN pip install --no-cache-dir -r /app/montaj/requirements.txt
COPY montaj /app/montaj

# Daimi məlumat (layihələr, orijinallar, işlər, modellər) — volume
ENV MONTAJ_DATA_DIR=/data \
    HF_HOME=/data/hf \
    MONTAJ_COOKIE_SECURE=1 \
    PYTHONUNBUFFERED=1
VOLUME ["/data"]
EXPOSE 4760

# Tək proses: işlər serverin içində işləyir və diskdə saxlanılır.
CMD ["python", "-m", "montaj", "--host", "0.0.0.0", "--port", "4760"]
