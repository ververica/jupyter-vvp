# jupyter-vvp

[![Build Status](https://travis-ci.com/ververica/jupyter-vvp.svg?token=oVi8ssiCvCkv55DAek4y&branch=master)](https://travis-ci.com/ververica/jupyter-vvp)

This extension to Jupyter lets you write and execute Flink SQL statements right from your Jupyter notebooks. 
It is backed by Ververica Platform's SQL REST API.

## Prerequisites

In order to use the Jupyter magics, you will require access to an installation of the Ververica Platform.

To set up Ververica Platform follow the instructions at https://docs.ververica.com/getting_started/index.html

## Compatibility

| Ververica Platform Version | Jupyter-VVP Version |
|----------------------------|---------------------|
| 2.3                        | 0.1.0               |

## Installation

The package can be installed from PyPi with 
```
pip install jupyter-vvp
```

Jupyter VVP comes with a custom kernel that extends `ipykernel` with code-completion for SQL Code through Ververica Platform.
In order to use the kernel you need to install it:
- First locate the installation directory of the package: `pip show jupyter-vvp`
- Go to the installation directory and install the kernel: `jupyter-kernelspec install jupytervvp/flinksqlkernel`

## Usage

### Loading the extension

From within IPython (`ipython3`) or an IPython3 kernel in any local Jupyter instance,
run
```
%load_ext jupytervpp
```
to load the extension and register the magics.

### Connecting to Ververica Platform

In order to use the Ververica Platform Jupyter magics, you will first need to connect to a Ververica Platform instance.
The `%connect_vvp` magic can be used for that:
```
%connect_vvp localhost --port 8080 --namespace default -s <your-session-name>
```

### SQL Statements

This will set up your notebook to communicate with the Ververica Platform.
We can test this by trying a DDL statement, e.g. to display all existing tables:
```
%%flink_sql
SHOW TABLES
```

The `flink_sql` magic can, of course, also be used to execute DML statements via the Ververica Platform:
```
%%flink_sql
CREATE TEMPORARY TABLE my_source_table (
id INT,
data STRING
) WITH (
'connector' = 'datagen'
);
CREATE TEMPORARY TABLE my_sink_table (
data STRING
) WITH (
'connector' = 'blackhole'
);
INSERT INTO my_sink_table SELECT data FROM my_source_table
```

### Examples

A few example notebook can be found in the [example_notebooks folder](./example_notebooks)

## Advanced Usage

### Sessions

A connection to a Ververica Platform instance is represented by a *session*, 
specifying its hostname and port,
and an API token if required.
The session has a name for convenient reference.

From within IPython (`ipython3`) or an IPython3 kernel in a Jupyter instance,
run
```
%connect_vvp localhost -p 8080 -n default -s mysession
```
This will connect and create a session with the name `mysession`.
The Ververica Platform host in this example is `localhost` and the port is `8080`.
The hostname should be the name under which Ververica Platform is accessible from the Jupyter server.
To connect to Ververica Platform through HTTPS, use the `--secure` (or `-S`) parameter.
In case Ververica Platform uses a self-signed certificate, it is possible to deactivate certificate checking using 
`--secure_self_signed` instead of `--secure`.
If no session exists then this session will be set as the default.

Session names are treated by the magics as strings.
The corresponding session object, with that name,
is found and taken from the local user context.

Session names can be listed by executing
```python
from vvpmagics import vvpsession
vvpsession.VvpSession.get_sessions()
```

When executing statements a session can be specified via:

```
%%flinksql mySession
...
```

#### Using API Tokens

- The argument `-k <API-Key>` (or `--key <API-Key>`) 
  will use the given value in `<API-Key>` as the API Key.
- To avoid having keys in notebooks, 
  the argument `-K` or `--prompt_key` can be specified,
  which asks the user to enter the key,
  and overrides any value specified by `-k`.

If no keys are specified, no API keys are used.

#### Examples:
```
%connect_vvp HOSTNAME -n default -s mySession -k 10504c2d-55f0-4969-ba83-26fad5f1640f
%connect_vvp HOSTNAME -n default -s mySession -K
```

### Substituting user variables

User variables defined in the notebook can be referenced in `flink_sql` cells.
To reference the variable, surround it with braces.
For example, setting

```python
topic_name = "myTopic"
```

allows the user (as in the example above) to do

```
%%flink_sql 

    .....

   ...: WITH ( 
   ...:     'connector.topic' = '{topic_name}', 

    .....

   ...: ) 
```

The cell is treated as a string,
and variables are replaced using Python's `string.format()` method,
so in principle all variables
that have a reasonable representation as a string can be used.
The scope is the `user_ns` dictionary,
accessed by Python via the IPython shell object.

Take care to avoid nesting braced expressions,
but note that double-brace placeholders may also be used (double-braced placeholders are used in the Flink configuration, 
for more information see the Flink configuration section below).


### Setting deployment parameters
Deployments of SQL INSERT jobs can be customised by setting parameters.
The possible settings keys are listed in a parameters dictionary in the example notebook,
and its use is shown there.
To use these parameters, the switch `-p [parameters-variable-name]` is used in the `flink_sql` Magic.
If no switch is specified, the default variable `vvp_default_parameters` is used.

You may find the following documentation generally useful:
- [Deployment Template settings](https://docs.ververica.com/user_guide/deployments/deployment_templates.html)
- [Lifecycle Management settings](https://docs.ververica.com/user_guide/lifecycle_management/index.html)

#### Important parameters

Please find some frequently used parameters below:

| Setting                               | Possible values                                               | Comment         | Documentation      |
|---------------------------------------|---------------------------------------------------------------|-----------------|--------------------|
|`metadata.name`                        | Arbitrary string                                              | If not specified, then this will be the cell contents. | |
|`metadata.annotations.license/testing` | Boolean: `True` or `False`                                    | The `flink_sql` magic will set this to `False` if not specified. | |
|`spec.template.spec.parallelism`       | Integer                                                       | | [Link](https://docs.ververica.com/user_guide/deployments/deployment_templates.html#parallelism-number-of-taskmanagers-and-slots) |
|`spec.restoreStrategy`                 | String: `"LATEST_STATE"`, `"LATEST_SAVEPOINT"`, or `"NONE"`.  | | [Link](https://docs.ververica.com/user_guide/lifecycle_management/index.html#restore-strategy) |
|`spec.upgradeStrategy`                 | String: `"STATELESS"`, `"STATEFUL"`, or `"NONE"`.             | | [Link](https://docs.ververica.com/user_guide/lifecycle_management/index.html#upgrade-strategy) |

#### Flink Configuration
In the deployment settings,
keys of the form 
```
spec.template.spec.flinkConfiguration.<FlinkConfigurationKey>
```
can be used.
The user can specify Flink configuration parameters in place of `<FlinkConfigurationKey>`.
For example, 
```
"spec.template.spec.flinkConfiguration.state.savepoints.dir": "s3://flink/savepoints"
```
See [here](https://docs.ververica.com/user_guide/deployments/configure_flink.html)
for deployment configuration documentation.

Note that the placeholders (e.g., `{{Namespace}}`) appearing in `flinkConfiguration` settings
are left untouched by `%%flink_sql`, so can be used as normal;
e.g.:
```
"spec.template.spec.flinkConfiguration.state.savepoints.dir": "s3://flink/savepoints/{{ namespace }}"
```
See [here](https://docs.ververica.com/administration/deployment_defaults.html#placeholders-in-flink-configuration)
for further details on placeholders.

### Error messages

Both the `%connect_vvp` and the `%%flink_sql` magics support the `-d/--debug` flag
to show full error messages.
In case of error results from the Ververica Platform it will display the full JSON response.  

### Code completion

When using the FlinkSql kernel, SQL queries in a `%%flink_sql` cell will be completed with suggestions from Ververica Platform.
In order for code completion to work, a connect_vvp session needs to exist. 
The default session will be used to communicate with Ververica Platform unless the another session is set for the `%%flink_sql` cell.
If any problems occur in the communication with Ververica Platform, code completion will attempt to use the standard Jupyter completion.

![Code Completion](completion.gif)


## Help
```
%connect_vvp?
```
and
```
%%flink_sql?
```
will show help texts for the magics.

## Bugs

Report an issue at https://github.com/ververica/jupyter-vvp/issues
