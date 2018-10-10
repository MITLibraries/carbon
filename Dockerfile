FROM python:3.6

ENV LD_LIBRARY_PATH /opt/lib/

RUN apt-get update && apt-get install -y unzip
RUN pip install --upgrade pip
RUN pip install pipenv
COPY vendor/libaio.so.1.0.1 /opt/lib/
RUN ln -s /opt/lib/libaio.so.1.0.1 libaio.so.1 && \
    ln -s /opt/lib/libaio.so.1 liaio.so
COPY vendor/instantclient-basiclite-linux.x64-18.3.0.0.0dbru.zip /
RUN unzip -j instantclient-basiclite-linux.x64-18.3.0.0.0dbru.zip -d /opt/lib/

COPY Pipfile* /
RUN pipenv install --system --deploy
COPY dist/carbon*.whl /
RUN pip install carbon*.whl

ENTRYPOINT ["carbon"]
CMD ["--help"]
