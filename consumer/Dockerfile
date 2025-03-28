# Use an official lightweight Python image.
FROM python:3.8-slim

# Set working directory
WORKDIR /app
COPY . /app
# Copy requirements.txt and install dependencies.
RUN pip install --no-cache-dir -r requirements.txt

# Copy your application code.
COPY main.py .

# Expose port 5000 for Flask.
EXPOSE 5000

# Run the application.
CMD ["python", "main.py"]
