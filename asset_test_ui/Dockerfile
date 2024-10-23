# Use an official Python runtime as a base image
FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port Streamlit runs on
EXPOSE 8550

# Command to run the Streamlit app
CMD ["streamlit", "run", "app.py", "--server.port", "8550"]
