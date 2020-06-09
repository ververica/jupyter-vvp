# vvp-magics

Experimental support for vvp using magics.

## Packaging

This can be done with
`python3 setup.py sdist`
in the same folder as `setup.py`.

The package can be installed with `pip3 install ./dist/vvpmagics-x.y.z.tar.gz`.


## Using

From within IPython (`ipython3`), run
```
%load_ext vvpmagics
%getConfig
```

to see the basic magic example.
