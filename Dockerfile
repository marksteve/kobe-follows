FROM ubuntu

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update

RUN apt-get -y install python-setuptools
RUN easy_install -U pip

RUN pip install requests
RUN pip install requests_oauthlib
RUN pip install schedule

ADD . /kobe-follows
WORKDIR /kobe-follows

CMD ["python", "-m", "kobe_follows"]
