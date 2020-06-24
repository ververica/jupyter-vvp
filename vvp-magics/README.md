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

## Help
```
%connect_vvp?
```
will show help text.
