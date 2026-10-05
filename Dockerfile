FROM node:22-alpine AS ui
WORKDIR /build
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build
FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY backend/ /app/backend/
COPY --from=ui /build/dist /app/frontend/dist
RUN useradd -m rover && mkdir -p /data && chown rover:rover /data
USER rover
ENV DATABASE_URL=sqlite:////data/rover.db
EXPOSE 8000
CMD ["python","-m","uvicorn","app.main:app","--app-dir","backend","--host","0.0.0.0","--port","8000"]
