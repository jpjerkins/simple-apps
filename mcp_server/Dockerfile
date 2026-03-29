FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy source into /app/mcp_server/ so it's importable as a package
COPY . ./mcp_server/

EXPOSE 8003

CMD ["python", "-m", "mcp_server.server"]
