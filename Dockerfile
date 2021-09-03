FROM python:3.9

ENV LD_LIBRARY_PATH /opt/lib/

RUN apt-get update && apt-get install -y unzip libaio1
RUN pip install --upgrade pip
RUN pip install pipenv
COPY vendor/instantclient-basiclite-linux.x64-18.3.0.0.0dbru.zip /
RUN unzip -j instantclient-basiclite-linux.x64-18.3.0.0.0dbru.zip -d /opt/lib/

COPY Pipfile* /
RUN pipenv install --system --deploy
COPY dist/carbon*.whl /
RUN pip install carbon*.whl

ENTRYPOINT ["carbon"]
CMD ["--help"]
