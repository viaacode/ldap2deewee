FROM python:3.7.6-alpine3.11

# Install postgresql-dev, gcc and musl-dev to be able to pip install psycopg2.
# Install postgresql to use in integration testing.
RUN apk add --no-cache postgresql-dev gcc musl-dev postgresql

# Copy all files
WORKDIR /src/usr/app
COPY . .

# Install packages
RUN pip3 install http://do-prd-mvn-01.do.viaa.be:8081/repository/pypi-internal/packages/viaa-chassis/0.0.4/viaa_chassis-0.0.4-py3-none-any.whl && \
    pip3 install -r requirements.txt && \
    pip3 install -r requirements-test.txt && \
    pip3 install flake8

# Postgresql initdb cannot be run as root.
RUN chown -R postgres:postgres /src && \
    chmod 777 /src

# Switch USER to non-root to be able to run initdb.
USER postgres

# Run the application
ENTRYPOINT ["python3"]
CMD ["app.py"]
