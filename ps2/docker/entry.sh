#!/bin/bash
# Role-based entrypoint for the PS2 lab image.
ROLE=${ROLE:-node}

ssh-keygen -A >/dev/null 2>&1

# Name resolution for networks without Docker DNS: HOSTS="web=10.0.0.1,app=10.0.0.2"
if [ -n "${HOSTS:-}" ]; then
  IFS=',' read -ra H <<< "$HOSTS"
  for e in "${H[@]}"; do echo "${e#*=} ${e%%=*}" >> /etc/hosts; done
fi

# Static routes (segmented lab): "dest via gw;dest via gw"
if [ -n "${ROUTES:-}" ]; then
  IFS=';' read -ra R <<< "$ROUTES"
  for r in "${R[@]}"; do ip route add $r 2>/dev/null || true; done
fi

# Optional host firewall (micro-segmentation), mounted by compose
[ -f /etc/host.nft ] && nft -f /etc/host.nft

/usr/sbin/sshd

case "$ROLE" in
  web)
    openssl req -x509 -newkey rsa:2048 -nodes -keyout /etc/nginx/k.pem -out /etc/nginx/c.pem \
      -days 30 -subj /CN=web >/dev/null 2>&1
    cat > /etc/nginx/http.d/default.conf <<'EOF'
server { listen 80; location / { return 200 "web ok\n"; } }
server {
  listen 443 ssl;
  ssl_certificate /etc/nginx/c.pem;
  ssl_certificate_key /etc/nginx/k.pem;
  location / { return 200 "web ok\n"; }
  location /api/ { proxy_pass http://app:8080/; }
}
EOF
    nginx
    ;;
  app)
    DBHOST=db python3 /opt/app.py &
    ;;
  db)
    mkdir -p /run/postgresql /var/lib/postgresql/data
    chown -R postgres:postgres /run/postgresql /var/lib/postgresql
    PGB=$(dirname "$(find /usr -name pg_ctl -type f 2>/dev/null | head -1)")
    su -s /bin/sh postgres -c "$PGB/initdb -D /var/lib/postgresql/data -A trust" >/dev/null 2>&1
    echo "listen_addresses='*'" >> /var/lib/postgresql/data/postgresql.conf
    echo "host all all 0.0.0.0/0 trust" >> /var/lib/postgresql/data/pg_hba.conf
    su -s /bin/sh postgres -c "$PGB/pg_ctl -D /var/lib/postgresql/data -l /tmp/pg.log start" >/dev/null 2>&1
    ;;
  files)
    mkdir -p /srv/public && echo "confidential payroll data" > /srv/public/secret.txt
    chmod -R a+rX /srv/public
    cat > /etc/samba/smb.conf <<'EOF'
[global]
  workgroup = LAB
  security = user
  map to guest = Bad User
  server min protocol = SMB2
[public]
  path = /srv/public
  guest ok = yes
  read only = yes
EOF
    smbd -D
    ;;
  jump)
    install -o admin -g admin -m 600 /opt/lab/id_ed25519 /home/admin/.ssh/id_ed25519
    ;;
  router)
    [ -f /etc/router.nft ] && nft -f /etc/router.nft
    ;;
esac

exec tail -f /dev/null
