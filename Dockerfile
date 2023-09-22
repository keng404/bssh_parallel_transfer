FROM python:3.10
WORKDIR /data
ENV STAGEDIR /data
COPY requirements.txt ${STAGEDIR}
RUN pip3 install --upgrade pip &&\
    pip3 install -r /data/requirements.txt
COPY pipeline_launcher.py ${STAGEDIR}/
COPY pipeline_launcher.rename.py ${STAGEDIR}/
COPY *.py ${STAGEDIR}/
COPY retry_requests_decorator.py /usr/local/lib/python3.10/site-packages/
ENV PATH $PATH:${STAGEDIR}