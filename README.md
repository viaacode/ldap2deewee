# ldap2deewee

Component that one-way syncs data from LDAP to a PostgreSQL DB in the deewee space. This allows for reporting further downstream.

The app is designed to sync changed (new/updated) LDAP entries to the PostgreSQL DB based on the `modifyTimestamp` attribute from LDAP. The identifying key between the two systems is the LDAP attribute `EntryUUID`.

Do note that the service is not able to handle deletes. A full load from LDAP can be achieved if the target database table is empty. So in case of known deleted LDAP entries that should reflect in the database, this mechanism can be used to "sync" up.

## Prerequisites

* Python >= 3.7 (when working locally)
* The package `python3-venv` (when working locally)
* The package `PostgreSQL` (when running integration tests locally)
* LDAP Server with appropriate structure
* PostgreSQL DB with appropriate schema
* Docker (optional)
* Access to the [meemoo PyPi](http://do-prd-mvn-01.do.viaa.be:8081/)

## Used libraries

* `viaa-chassis`
* `ldap3` - communicates with the LDAP server
* `psycopg2` - communicates with the PostgreSQL server

### Testing

* `pytest` - runs automated tests
* `pytest-cov` - produces coverage reports
* `testing.postgresql` - creates temporary PostgreSQL databases and cleans up afterwards

## Usage

First clone this repository with `git clone` and change into the new directory.

If you have no access to an LDAP and/or PostgreSQL server they can easily be set up internally by using Docker containers, explained in section [external servers via containers](#external-servers-via-containers).

### Locally

Running the app locally is recommended when developing/debugging and running tests.

First create the virtual environment:

```shell
python3 -m venv ./venv
```

Be sure to activate said environment:

```shell
source ./venv/bin/activate
```
Now we can install the required packages:

```shell
pip3 install -r requirements.txt
```

Copy the `config.yml.example` file:

```shell
cp ./config.yml.example ./config.yml
```

Be sure to fill in the correct configuration parameters in `config.yml` in order to communicate with the LDAP server and PostgreSQL database.

Run the app:

```shell
python3 -m app.app
```

#### Testing

To run the tests, first install the testing dependencies:

```shell
pip3 install -r requirements-test.txt
```

Run the tests:

```shell
python3 -m pytest
```

The deewee integration tests make use of the PostgreSQL command `initdb` to create a temporary database. Thus, in order the run those integration tests you need to have `PostgreSQL` installed.

If desired, you can also run coverage reports:

```shell
python3 -m pytest "--cov=app.app" "--cov=app.comm"
```

### External servers via containers

If you have no access to an LDAP and/or PostgreSQL server they can easily be set up internally by using Docker containers.

#### LDAP Container

A container which runs an LDAP server with an empty structure can be found [here](https://github.com/viaacode/docker-openldap-sc-idm "docker-openldap-sc-idm"). The custom `objectClasses` and `attributeTypes` can be found [here](https://github.com/viaacode/viaa-ldap-schema "viaa-ldap-schema"). The latter repository also contains a `sample.ldif` file with some `orgs` and `persons`.

#### PostgreSQL Container

A Dockerfile can be found in `./additional_containers/postgresql`. The schema is defined in the `init.sql` file of said folder.

Create an `env` file and fill in the parameters:

```shell
cp ./additional_containers/postgresql/env.example ./additional_containers/postgresql/env
```

Afterwards build and run the container:

```shell
docker build -f ./additional_containers/postgresql/Dockerfile -t deewee_postgresql .
docker run --name deewee_postgresql -p 5432:5432 --env-file=./additional_containers/postgresql/env -d deewee_postgresql
```

If desired, test the connection with the following statement in terminal:

```shell
psql -h localhost -U {postgresql_user} -d {postgresql_database}
```

### Container

If you just want to execute the app it might be easier to run the container instead of installing python and dependencies.

Copy the config file (`cp ./config.yml.example ./config.yml`) and fill in the correct parameters:

If the app connects to external servers just build the image:

```shell
docker build -t ldap2deewee .
```

If the build succeeded, you should be able to find the image via:

```shell
docker image ls
```

To run the app in the container, just execute:

```shell
docker run --name ldap2deewee -d ldap2deewee
```

If you want to run the tests in the container, you can run the container in interactive mode:

```shell
docker run -it --rm --entrypoint=/bin/sh ldap2deewee
```

You can then run the tests as described in section [testing](#testing-1).

However, if you make use of the other (LDAP and PostgreSQL) containers as described above, the app container needs to able to communicate with them. In order to do so you can connect them via a `Docker Network`. We can do this manually by creating a Docker Network and connecting them. Another more automatic option is via `Docker Compose`.

#### Docker Network

We'll need to create a network and connect the containers together:

```shell
docker network create ldap2deewee_network
docker network connect ldap2deewee_network deewee_postgresql
docker network connect ldap2deewee_network archief_ldap
```

Now we just need to build the ldap2deewee container and run in the Docker Network. Make sure that the host parameters in the `config.yml` file actually point to within the Docker Network.

```shell
docker build -t ldap2deewee .
docker run --name ldap2deewee --network=ldap2deewee_network -d ldap2deewee
```

Check the status via `docker container ls -a` and/or check the logs via `docker logs ldap2deewee`.

#### Docker Compose

Instead of manually creating a network and coupling the containers together, Docker Compose can be used as a more automatic alternative.

Do **note** that how the docker-compose file is set up, the process expects the PostgreSQL and LDAP images to have been build locally. However, as the Docker Compose process will also run the containers, make sure that they do not exist yet.

If you haven't already, be sure to create an `env` file for OpenLDAP and PostgreSQL containers as the Docker Compose process depends on such files. See the respective `env.example` files for the desired structure.

```shell
docker-compose up -d
```
Check the status via `docker container ls -a` and/or check the logs via `docker logs ldap2deewee`