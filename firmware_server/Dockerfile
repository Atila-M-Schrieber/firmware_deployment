FROM python:3.12
WORKDIR /code
COPY requirements.txt .
RUN pip install -r requirements.txt
CP src/ .
EXPOSE 80/tcp
EXPOSE 22222/tcp
CMD ["python", "./server.py"]
