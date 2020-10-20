FROM jupyter/scipy-notebook

COPY dist/jupyter-vvp-0.1.0.tar.gz /tmp/
COPY example_notebooks/QuickStart.ipynb work/
COPY jupytervvp/flinksqlkernel /tmp/flinksqlkernel

RUN sed -i "s|localhost|vvp-gateway|g" work/QuickStart.ipynb

RUN pip install /tmp/jupyter-vvp-0.1.0.tar.gz
RUN jupyter kernelspec install --user /tmp/flinksqlkernel