FROM postgres:17-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-venv tini ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 1000 learner \
    && python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}" PYTHONUNBUFFERED=1 TZ=Europe/Moscow \
    SQLTRAINER_HOST=127.0.0.1 SQLTRAINER_PORT=5432 \
    PGHOST=127.0.0.1 PGPORT=5432 PGUSER=sqltrainee PGDATABASE=sqltrainee
COPY docker/requirements.txt /opt/requirements.txt
RUN pip install --no-cache-dir -r /opt/requirements.txt
COPY . /opt/sqltrainee
RUN chmod +x /opt/sqltrainee/docker/psql.sh \
    && ln -s /opt/sqltrainee/docker/psql.sh /usr/local/bin/trainer-psql
WORKDIR /var/lib/sqltrainee/work
EXPOSE 8888
VOLUME ["/var/lib/sqltrainee"]
HEALTHCHECK --interval=15s --timeout=5s --start-period=90s --retries=4 \
    CMD python /opt/sqltrainee/docker/runtime.py health
ENTRYPOINT ["/usr/bin/tini", "--", "python", "/opt/sqltrainee/docker/runtime.py"]
CMD ["serve"]
