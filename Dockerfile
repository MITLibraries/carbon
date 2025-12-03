FROM python:3.12-slim

# Set path for Oracle client libraries
ENV LD_LIBRARY_PATH=/opt/lib/

RUN apt-get update && apt-get upgrade -y

# Install Oracle dependencies
RUN apt-get install -y unzip libaio1t64
RUN ln -s /usr/lib/x86_64-linux-gnu/libaio.so.1t64 /usr/lib/libaio.so.1
COPY vendor/instantclient-basiclite-linux.x64-21.9.0.0.0dbru.zip /
RUN unzip -j instantclient-basiclite-linux.x64-21.9.0.0.0dbru.zip -d /opt/lib/

# Install Python dependencies
RUN pip install --upgrade pip pipenv
COPY . .
RUN pipenv install

ENTRYPOINT ["pipenv", "run", "carbon"]
