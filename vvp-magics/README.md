# vvp-magics

Experimental support for vvp using magics.
Currently just a prototype.
This calls two of the `/namespace` endpoints
to show that we can send calls and display the response as text.

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
%vvp_connect localhost 
```
This will list the available namespaces.
```
%vvp_connect?
```
will show help text including how to specify the namespace and port.
If a namespace is specified then just that namespace will be called.
The request URL used is shown.

```
%vvp_connect localhost -n default -s mysession
```
This will connect and create a session with the name mysession.
If no session exists then this will be the default.


## Catalog SQL requests
```
%%execute_catalog_statement mySession 
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
This will return the HTTP response code from the back end.

Note: the `mySession` variable is actually referenced 
by treating its input to the magic as a string 
and finding the object from the local user scope by name.