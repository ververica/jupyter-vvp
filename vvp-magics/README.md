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


## Using

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

At present this is just a simple HTTP request that displays the text response that it receives.
