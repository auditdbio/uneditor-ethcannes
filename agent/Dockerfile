# 1. Base Image
FROM python:3.13-slim

# 2. Install uv, our package manager
RUN pip install uv

# 3. Set up the working directory in the container
WORKDIR /app

# 4. Copy local dependency source code first.
# These paths are relative to the Docker build context, which is the project root.
COPY ./models /app/models

# 5. Copy the main application source code.
COPY ./agent /app/agent

# 6. Set the working directory to the main application's root for installation.
WORKDIR /app/agent

# 7. Install all Python dependencies using uv.
# uv is smart enough to detect the workspace and find the local 'models' package.
RUN uv pip install --system .

# 8. Expose the port the app runs on.
EXPOSE 8000

# 9. Define the command to run the application.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 