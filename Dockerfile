FROM jupyter/scipy-notebook

COPY dist/jupyter_vvp-0.0.1.tar.gz /tmp/
COPY example_notebooks/QuickStart.ipynb work/
COPY jupytervvp/flinksqlkernel /tmp/flinksqlkernel
>>>>>>> [VVP-2594] Update name of notebook copied into Dockerfile

RUN sed -i "s|localhost|vvp-gateway|g" work/QuickStart.ipynb

RUN pip install /tmp/jupyter_vvp-0.0.1.tar.gz
RUN jupyter kernelspec install --user /tmp/flinksqlkernel