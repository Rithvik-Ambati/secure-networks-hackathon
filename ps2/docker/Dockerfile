FROM alpine:3.19
# One small image for every lab node; the role is chosen at start by ROLE=...
RUN apk add --no-cache bash openssh openssh-client sshpass nmap samba samba-client \
      nginx openssl postgresql16 python3 curl nftables iproute2 tcpdump \
      netcat-openbsd libcap conntrack-tools \
 && adduser -D -s /bin/bash admin && echo "admin:$(head -c12 /dev/urandom | base64)" | chpasswd \
 && adduser -D -s /bin/bash dbadmin && echo "dbadmin:Password123" | chpasswd \
 && adduser -D -s /bin/bash svc && echo "svc:Password123" | chpasswd \
 && mkdir -p /opt/lab /home/admin/.ssh \
 && ssh-keygen -q -t ed25519 -N '' -C lab-admin -f /opt/lab/id_ed25519 \
 && cp /opt/lab/id_ed25519.pub /home/admin/.ssh/authorized_keys \
 && chown -R admin:admin /home/admin/.ssh && chmod 700 /home/admin/.ssh && chmod 600 /home/admin/.ssh/authorized_keys \
 && printf '\nPasswordAuthentication yes\nPermitRootLogin no\n' >> /etc/ssh/sshd_config
COPY app.py /opt/app.py
COPY entry.sh /entry.sh
RUN chmod +x /entry.sh
ENTRYPOINT ["/entry.sh"]
