FROM python:latest as compile-image

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY . /tribun
WORKDIR /tribun

RUN pip install .

FROM python:latest as build-image

RUN mkdir /tribun_scripts

COPY docker-entrypoint.sh /usr/local/bin/
COPY --from=compile-image /opt/venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["docker-entrypoint.sh"]

CMD ["python"]
