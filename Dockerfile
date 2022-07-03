FROM python:3.10.5-slim-buster

ENV TZ="Asia/Shanghai"

RUN mkdir /app

ADD . /app

WORKDIR /app

RUN pip install -r requirements.txt

CMD ["python","-u","main.py"]

