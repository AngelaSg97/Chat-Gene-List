# Use an official Python image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy requirements file and install dependencies using standard pip.
# This ensures maximum compatibility and avoids "command not found" errors like 'uv'.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt 

# Copy the Streamlit application file
COPY gene_chat_app.py .

# Streamlit defaults to port 8501
EXPOSE 8501

# Command to run the Streamlit application.
# It must be executed with necessary environment variables (e.g., GEMINI_API_KEY).
CMD ["streamlit", "run", "gene_chat_app.py", "--server.port=8501", "--server.enableCORS=true", "--server.enableXsrfProtection=false"]