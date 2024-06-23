FROM python:3.12
WORKDIR /code
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY src/ .

RUN mkdir /firmware
ENV FIRMWARE_DIRECTORY=/firmware

# Public signing key - authentication (especially with multiple signers)
# should be done with a more integrated authentication solution
# (or at least Docker Secrets), but storing the public key in an
# environment variable is sufficient for this example.
ENV PUBLIC_KEY="-----BEGIN PGP PUBLIC KEY BLOCK-----\
mDMEZngLohYJKwYBBAHaRw8BAQdA5d9WZrE/gV+vlQM2mxFsjVwhM05GLzl/mIAB\
SGF4YMK0G0pvaG4gRG9lIDxqb2huQGV4YW1wbGUuY29tPoiZBBMWCgBBFiEE3dFC\
lBSY6tWWH6nXM5TKrFyfa7oFAmZ4C6ICGwMFCQWjmoAFCwkIBwICIgIGFQoJCAsC\
BBYCAwECHgcCF4AACgkQM5TKrFyfa7rbJgD/VX3E132RKKO7V7Xx7Jpo0EHhqSCK\
p7PfNcsYvjE7WAAA/iI0+aFqKhMDMc5FpO5/mm2I+S0HITMp5W0AuaE/2pMLuDgE\
ZngLohIKKwYBBAGXVQEFAQEHQIwr9DfUrvMGVXdkmH3ybe2XIn7Yp2Pnoddu6/SI\
N0dtAwEIB4h+BBgWCgAmFiEE3dFClBSY6tWWH6nXM5TKrFyfa7oFAmZ4C6ICGwwF\
CQWjmoAACgkQM5TKrFyfa7q8gQD+OlXI3z0thy+xd1b/Hy3vZBoxA7qzcotN4x6g\
bgQCeQ0BANcjuFR/hJ2mK84HOs3Af9Adfs9tQhQTF5pEld45lmUI\
=QZYs\
-----END PGP PUBLIC KEY BLOCK-----"

# Also not the best way to store known ID's, and should be able to add new ID's in a webui
ENV KNOWN_IDS=-2:-1:example

# This should be changed for a remote deployment
EXPOSE 8000/tcp
CMD ["python", "./app.py"]
