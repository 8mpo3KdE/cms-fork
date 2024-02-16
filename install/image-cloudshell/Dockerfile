FROM centos-stream-9:20230918

RUN rm -f /etc/yum.repos.d/*
ADD depot.repo /etc/yum.repos.d/
RUN dnf install -y python3 python3-openstackclient openssh-server
RUN /usr/bin/ssh-keygen -q -t ecdsa -f /etc/ssh/ssh_host_ecdsa_key -C '' -N ''
RUN /usr/bin/ssh-keygen -q -t rsa -f /etc/ssh/ssh_host_rsa_key -C '' -N ''
RUN /usr/bin/ssh-keygen -q -t ed25519 -f /etc/ssh/ssh_host_ed25519_key -C '' -N ''

EXPOSE 22
