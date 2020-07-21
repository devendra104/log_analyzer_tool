FROM python:3.6-alpine
WORKDIR /root
RUN apk add --no-cache gcc musl-dev linux-headers build-base python3-dev libevent-dev openssl-dev libffi-dev gzip openssh
EXPOSE 22
RUN pip install virtualenv
RUN ssh-keygen -f ~/.ssh/id_rsa -P ""
RUN virtualenv -p python3.6 pyenvi
COPY . . && ~/.ssh/id.rsa securecontent.pem
CMD source pyenvi/bin/activate && chmod 400 securecontent.pem
RUN pip install -r requirements.txt
CMD ["python", "rest_service.py"]