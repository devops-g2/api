FROM python:3.11-slim

# Set the working directory to /app
WORKDIR /app

# Copy the entire project directory to the container
COPY . .

# Install Poetry and project dependencies
RUN pip install poetry
# RUN poetry config virtualenvs.create false
RUN poetry install --no-dev

# Start the server
ENTRYPOINT [ "poetry", "run", "poe" ]


