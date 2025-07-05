# 1. Base Image
FROM python:3.13-slim

# 2. Set Environment Variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 3. Install uv
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir uv

# 4. Set Workdir
WORKDIR /app

# 5. Copy dependency files and install dependencies
COPY pyproject.toml uv.lock ./
RUN uv pip sync --no-cache uv.lock

# 6. Copy application code
COPY demo_uagent/ ./demo_uagent/

# 7. Set the command to run the application
CMD ["uv", "run", "python", "-m", "demo_uagent.agent"] 