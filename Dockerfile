FROM python:3.12.1

# Install Poetry
RUN pip install --upgrade pip
RUN pip install poetry

# Set the working directory in the container
WORKDIR /app

# Copy the project files to the container
COPY pyproject.toml poetry.lock /app/

# Install dependencies
RUN poetry config virtualenvs.create false
RUN poetry install --no-interaction --no-ansi

# Copy the rest of your app's code
COPY . /app

# Command to run the application
CMD ["poetry", "run", "python", "manage.py", "runserver", "0.0.0.0:8000"]