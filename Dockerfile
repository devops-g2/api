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
CMD ["poetry", "run", "task", "start"]
# # CMD [ "poetry", "shell" ]
# # CMD [ "task", "start" ]
# CMD [ "poetry", "run", "uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4" ]

