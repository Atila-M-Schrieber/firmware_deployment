FROM python:3.12
WORKDIR /code
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY src/ .

# This should be changed for a remote deployment
EXPOSE 8000/tcp
CMD ["python", "./app.py"]
