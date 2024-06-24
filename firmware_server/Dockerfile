FROM python:3.12
WORKDIR /code

COPY requirements.txt .
RUN pip install -r requirements.txt

RUN mkdir /firmware
ENV FIRMWARE_DIRECTORY=/firmware

# Should be longer in production
ENV UPDATE_EXPIRACY_MINUTES=1

# Public signing key - authentication (especially with multiple signers)
# should be done with a more integrated authentication solution
# (or at least Docker Secrets), but storing the public key in an
# copied file is sufficient for this example.
COPY public.asc /firmware/keys/

# Also not the best way to store known ID's, and should be able to add new ID's in a webui
ENV KNOWN_IDS=example
ENV KNOWN_TEST_IDS=-2:-1:test_id

# This should be changed for a remote deployment
EXPOSE 8000/tcp

COPY src/ .
CMD ["python", "./app.py"]
