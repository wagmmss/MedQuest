FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip pip install -r requirements.txt gunicorn

# Keep the large, rarely-changing image corpus in its own layer. A backend code
# change can then publish and download only the small source layers below.
COPY static ./static
COPY data ./data
COPY scripts ./scripts
COPY api ./api
COPY migrations ./migrations
COPY *.py ./
COPY *.json ./
COPY *.txt ./

ENV PORT=8000
ENV PYTHONUNBUFFERED=1
EXPOSE 8000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "--timeout", "120", "api:create_app()"]
