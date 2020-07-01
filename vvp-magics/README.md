# vvp-magics

[![Build Status](https://travis-ci.com/dataArtisans/vvp-jupyter.svg?token=RGozj1rgTPauwuugxzZx&branch=master)](https://travis-ci.com/dataArtisans/vvp-jupyter)

Experimental support for vvp using IPython Magics commands.

## Packaging

This can be done with
`python3 setup.py sdist`
in the same folder as `setup.py`.

The package can be installed with `pip3 install ./dist/vvpmagics-x.y.z.tar.gz`.


## Sessions

From within IPython (`ipython3`) or an IPython3 kernel in a local Jupyter instance,
run
```
%load_ext vvpmagics
%connect_vvp localhost 
```
to 
 1. load the extension; and
 2. list the available namespaces.
 
If a namespace is specified then just that namespace will be called.
The request URL used is shown.

```
%connect_vvp localhost -n default -s mysession
```
This will connect and create a session with the name mysession.
If no session exists then this will be the default.

## Setting deployment parameters
Deployments of SQL INSERT jobs can be customised by setting parameters.
The possible settings keys are listed in a parameters dictionary in the example notebook,
and its use is shown there.
To use these parameters, the switch `-p [parameters-variable-name]` is used in the `flink_sql` Magic.
If no switch is specified, the default variable `vvp_default_parameters` is used.

### Possible deployment setting values
Users may find the following documentation generally useful:
- [Deployment Template settings](https://docs.ververica.com/user_guide/deployments/deployment_templates.html)
- [Lifecycle Management settings](https://docs.ververica.com/user_guide/lifecycle_management/index.html)

Some relevant examples include:
- `metadata.name`: The name of the deployment.
  This can be any string.
  If not specified, then this will be the contents of the cell.
- `metadata.annotations.license/testing`: can be `True` or `False`.
   The `flink_sql` magic will set this to `False` if not specified.
- `spec.template.spec.parallelism`: integer value. 
   See [here](https://docs.ververica.com/user_guide/deployments/deployment_templates.html#parallelism-number-of-taskmanagers-and-slots).
-  `spec.restoreStrategy`: Can be `"LATEST_STATE"`, `"LATEST_SAVEPOINT"`, or `"NONE"`.
   See [here](https://docs.ververica.com/user_guide/lifecycle_management/index.html#restore-strategy)
-  `spec.upgradeStrategy`: Can be `"STATELESS"`, `"STATEFUL"`, or `"NONE"`.
   See [here](https://docs.ververica.com/user_guide/lifecycle_management/index.html#upgrade-strategy)
-  `spec.template.spec.flinkConfiguration.<FlinkConfigurationKey>`: 
   The user can specify Flink configuration parameters in place of `<FlinkConfigurationKey>`.
   For example, `spec.template.spec.flinkConfiguration.state.savepoints.dir: "s3://flink/savepoints"`.
   See [here](https://docs.ververica.com/user_guide/deployments/configure_flink.html).
   Note that the placeholders (e.g., `{{Namespace}}`) appearing in `flinkConfiguration` settings
   are not processed by `%%flink_sql` so can be used as normal:
   see [here](https://docs.ververica.com/administration/deployment_defaults.html#placeholders-in-flink-configuration).

## SQL requests
```
%%flink_sql mySession 
   ...: CREATE TABLE `testTable2` ( 
   ...:   id bigint 
   ...:   -- Watermark definition, here for a timestamp column 'ts' 
   ...:   -- WATERMARK FOR ts AS ts - INTERVAL '1' MINUTE 
   ...: ) 
   ...: -- Free text comment 
   ...: COMMENT '' 
   ...: WITH ( 
   ...:   -- Kafka connector configuration. See documentation for all configuration options. 
   ...:     'connector.type' = 'kafka', 
   ...:     'connector.version' = 'universal', 
   ...:     'connector.topic' = 'testTopic', 
   ...:     'connector.properties.bootstrap.servers' = 'localhost:9092', 
   ...:     'connector.properties.group.id' = '...', 
   ...:     'connector.startup-mode' = 'earliest-offset' 
   ...: ) 

```
This will return the HTTP response body from the back end.
If there is a `resultsTable` object then this will be returned as a Pandas Dataframe.

Note: the `mySession` variable is actually referenced 
by treating its input to the magic as a string 
and finding the object from the local user scope by name.

## Further examples

See the example notebooks:

- [Connect to VVP](./example_notebooks/ConnectToVVP.test.ipynb)
- [DDL and DML commands and queries](./example_notebooks/FlinkSql.test.ipynb)

## Docker setup

First build the vvpmagics.zip. Then create the Docker image:
```
docker build . --tag vvp-jupyter:latest
```
Finally run docker compose to set vvp environment up:
```
docker-compose up vvp-gateway vvp-appmanager vvp-ui vvp-jupyter
```

To log into Jupyter, look into the docker compose output and find a line that looks like this:
```
http://127.0.0.1:8888/?token=814a4f1ef6a10328f25e67aeb9e5d67e381aff0b2fc7ad2b
```

In the notebook use vvp-gateway as hostname and 8080 as port. An example notebook can be found in the work folder.

## Help
```
%connect_vvp?
```
will show help text.
