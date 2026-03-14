FROM python:3.11-slim

WORKDIR /app

# Install Python dependencies first (layer-cached)
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy platform and app source code
COPY backend/ ./backend/
COPY apps/ ./apps/
COPY platform/ ./platform/
COPY conftest.py ./

# Data dirs are created on first run by AppDatabase.init(); nothing to pre-create.

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
