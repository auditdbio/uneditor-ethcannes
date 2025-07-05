# 1. Base Image
FROM python:3.13-slim

# 3. Install uv
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir uv

# 4. Set Workdir
WORKDIR /app

# 5. Copy dependency files and install dependencies
COPY pyproject.toml uv.lock ./
RUN uv venv
RUN uv pip install -e . --no-cache

# 6. Copy application code
COPY demo_uagent/ ./demo_uagent/

# 7. Set the command to run the application
CMD ["uv", "run", "python", "-m", "demo_uagent.agent"] 