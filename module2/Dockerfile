FROM python:3.8

WORKDIR /app

COPY requirements.txt ./

RUN pip install -r requirements.txt

COPY ./src/module2.py ./

CMD [ "python", "-u", "./module2.py"]