# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

RUN apt-get update && apt-get install -y ffmpeg

# Install Pipenv
RUN pip install pipenv

# Copy the Pipfile and Pipfile.lock into the container
COPY Pipfile Pipfile.lock /app/

# Install dependencies from Pipfile.lock
RUN pipenv install --deploy --ignore-pipfile

# Copy the rest of your app's source code from your host to your image filesystem.
COPY . /app

# The CMD should use Pipenv to run the Flask app
CMD ["pipenv", "run", "python", "./app.py"]
