# Use shared base image with all dependencies pre-installed
FROM estoque-ddi-base:latest

# Copy application source code
COPY src/ ./src/

# Command to run the application
CMD ["python", "src/service.py"]
