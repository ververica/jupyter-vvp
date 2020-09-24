FROM jupyter/scipy-notebook

COPY dist/jupyter_vvp-0.0.1.tar.gz /tmp/
COPY example_notebooks/FlinkSql.test.ipynb work/
COPY flinksqlkernel /tmp/flinksqlkernel

RUN sed -i "s|localhost|vvp-gateway|g" work/FlinkSql.test.ipynb

RUN pip install /tmp/jupyter_vvp-0.0.1.tar.gz
RUN jupyter kernelspec install --user /tmp/flinksqlkernel