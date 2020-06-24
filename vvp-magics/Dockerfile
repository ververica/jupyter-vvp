FROM jupyter/scipy-notebook

COPY dist/vvpmagics-0.0.1.tar.gz /tmp/
COPY example_notebooks/FlinkSql.test.ipynb work/

RUN sed -i "s|localhost|vvp-gateway|g" work/FlinkSql.test.ipynb

RUN pip install /tmp/vvpmagics-0.0.1.tar.gz
