FROM python:3.13-slim

# Pull in OS security fixes released since the base image was built.
RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

# Run as an unprivileged user so a compromise of the app is not root in the container.
RUN useradd --uid 10001 --no-create-home app
WORKDIR /srv
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ .
USER 10001
EXPOSE 8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
