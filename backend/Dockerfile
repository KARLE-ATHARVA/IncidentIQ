FROM python:3.14-slim

WORKDIR /app

COPY backend/requirements.txt ./backend/requirements.txt

RUN pip install --no-cache-dir -r ./backend/requirements.txt

COPY backend/app ./backend/app
COPY backend/alembic.ini ./backend/alembic.ini
COPY backend/alembic ./backend/alembic

EXPOSE 8000

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]