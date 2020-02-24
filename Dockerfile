FROM python:3.7.6-buster

WORKDIR /src/usr/app
COPY . .

RUN pip3 install http://do-prd-mvn-01.do.viaa.be:8081/repository/pypi-internal/packages/viaa-chassis/0.0.4/viaa_chassis-0.0.4-py3-none-any.whl && pip3 install -r requirements.txt

# Run the application
ENTRYPOINT ["python"]
CMD ["app.py"]