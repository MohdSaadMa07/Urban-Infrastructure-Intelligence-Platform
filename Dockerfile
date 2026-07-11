FROM python:3.12-slim-bookworm AS backend

RUN apt-get update && apt-get install -y --no-install-recommends \
    gdal-bin \
    libgdal-dev \
    binutils \
    && rm -rf /var/lib/apt/lists/*

ENV GDAL_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu/libgdal.so
ENV GEOS_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu/libgeos_c.so

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

# --- Build frontend ---
FROM node:20-bookworm AS frontend
WORKDIR /app
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ .
RUN npm run build

# --- Final image ---
FROM backend AS final
RUN mkdir -p /frontend
COPY --from=frontend /app/dist /frontend/dist
RUN chmod +x entrypoint.sh

EXPOSE 8000

CMD ./entrypoint.sh
