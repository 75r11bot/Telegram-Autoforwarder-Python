# Use the official Python image from the Docker Hub
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the required dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code into the container
COPY . .

# Ensure the sessions directory exists and has appropriate permissions
RUN mkdir -p /app/sessions && chmod -R 777 /app/sessions

# Expose the port your app runs on
EXPOSE 8000

# Run the application
CMD ["python", "main.py"]
