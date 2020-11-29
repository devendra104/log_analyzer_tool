FROM registry.access.redhat.com/rhscl/python-36-rhel7
USER 0
RUN yum install -y gcc && yum repolist
WORKDIR /root
EXPOSE 22
RUN pip install --upgrade pip
RUN pip install kaleido
RUN pip install virtualenv
RUN python3.6 --version
RUN virtualenv -p python3.6 pyenvi
COPY . .
# id_rsa, for access the host machine
CMD source pyenvi/bin/activate && chmod 400 id_rsa
RUN pip install -r requirements.txt
CMD ["python", "rest_service.py"]
