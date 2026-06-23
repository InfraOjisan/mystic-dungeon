#!/usr/bin/env bash
set -euo pipefail

VM_NAME="lub_wp_test"
VM_HOSTNAME="lub-wp-test"
VM_IP="192.168.122.50"
VM_MAC="52:54:00:24:04:50"
VM_RAM_MB="4096"
VM_VCPUS="2"
VM_DISK_SIZE="10G"

IMAGE_DIR="/var/lib/libvirt/images"
BASE_IMAGE="${IMAGE_DIR}/noble-server-cloudimg-amd64.img"
BASE_IMAGE_URL="https://cloud-images.ubuntu.com/noble/current/noble-server-cloudimg-amd64.img"
DISK_IMAGE="${IMAGE_DIR}/${VM_NAME}.qcow2"
SEED_ISO="${IMAGE_DIR}/${VM_NAME}-seed.iso"
SSH_KEY="/home/pandalex/.ssh/${VM_NAME}_ed25519"

WP_ADMIN_USER="AdminPandalex"
WP_ADMIN_PASS="wpAdmin001Pass"
WP_ADMIN_EMAIL="admin@example.test"
WP_SITE_TITLE="lub_wp_test"

if [ "$(id -u)" -ne 0 ]; then
  echo "This script must run as root." >&2
  exit 1
fi

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Missing required command: $1" >&2
    exit 1
  }
}

need_cmd virsh
need_cmd virt-install
need_cmd qemu-img
need_cmd genisoimage
need_cmd wget
need_cmd ssh-keygen
need_cmd ssh
need_cmd curl

mkdir -p "$IMAGE_DIR"

if [ ! -f "$SSH_KEY" ]; then
  install -d -m 700 -o pandalex -g pandalex /home/pandalex/.ssh
  sudo -u pandalex ssh-keygen -t ed25519 -N "" -f "$SSH_KEY" -C "${VM_NAME}@homeserverxeon" >/dev/null
fi
SSH_PUBKEY="$(cat "${SSH_KEY}.pub")"

if [ ! -s "$BASE_IMAGE" ]; then
  echo "Downloading Ubuntu 24.04 cloud image to ${BASE_IMAGE}"
  tmp_base="${BASE_IMAGE}.tmp"
  wget -O "$tmp_base" "$BASE_IMAGE_URL"
  mv "$tmp_base" "$BASE_IMAGE"
fi

virsh net-start default >/dev/null 2>&1 || true
virsh net-autostart default >/dev/null 2>&1 || true

if ! virsh net-dumpxml default | grep -q "ip='${VM_IP}'"; then
  virsh net-update default add ip-dhcp-host \
    "<host mac='${VM_MAC}' name='${VM_NAME}' ip='${VM_IP}'/>" \
    --live --config
fi

if ! virsh dominfo "$VM_NAME" >/dev/null 2>&1; then
  if [ -e "$DISK_IMAGE" ]; then
    echo "Disk already exists but domain does not: ${DISK_IMAGE}" >&2
    echo "Move or remove it before recreating ${VM_NAME}." >&2
    exit 1
  fi

  qemu-img convert -O qcow2 "$BASE_IMAGE" "$DISK_IMAGE"
  qemu-img resize "$DISK_IMAGE" "$VM_DISK_SIZE"
  chown libvirt-qemu:kvm "$DISK_IMAGE"
  chmod 0600 "$DISK_IMAGE"

  workdir="$(mktemp -d)"
  trap 'rm -rf "$workdir"' EXIT

  cat >"${workdir}/meta-data" <<EOF_META
instance-id: ${VM_NAME}-$(date +%s)
local-hostname: ${VM_HOSTNAME}
EOF_META

  cat >"${workdir}/user-data" <<'EOF_USER_DATA'
#cloud-config
hostname: __VM_HOSTNAME__
manage_etc_hosts: true
ssh_pwauth: false
disable_root: true

users:
  - default
  - name: pandalex
    gecos: pandalex
    groups: [adm, sudo]
    sudo: ALL=(ALL) NOPASSWD:ALL
    shell: /bin/bash
    lock_passwd: true
    ssh_authorized_keys:
      - __SSH_PUBKEY__

package_update: true
package_upgrade: false

write_files:
  - path: /root/install-wordpress.sh
    owner: root:root
    permissions: '0755'
    content: |
      #!/usr/bin/env bash
      set -euo pipefail
      export DEBIAN_FRONTEND=noninteractive

      apt-get update
      apt-get install -y \
        ca-certificates curl nginx mysql-server \
        php-fpm php-mysql php-curl php-gd php-mbstring php-xml php-zip unzip

      systemctl enable --now mysql
      systemctl enable --now nginx

      mysql <<'SQL'
      CREATE DATABASE IF NOT EXISTS wordpress DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
      CREATE USER IF NOT EXISTS 'wpuser'@'localhost' IDENTIFIED BY '__WP_DB_PASS__';
      ALTER USER 'wpuser'@'localhost' IDENTIFIED BY '__WP_DB_PASS__';
      GRANT ALL PRIVILEGES ON wordpress.* TO 'wpuser'@'localhost';
      FLUSH PRIVILEGES;
      SQL

      install -d -m 0755 -o www-data -g www-data /var/www/wordpress
      if [ ! -f /var/www/wordpress/wp-settings.php ]; then
        curl -fsSL --retry 5 --retry-delay 5 https://wordpress.org/latest.tar.gz \
          | tar -xz --strip-components=1 -C /var/www/wordpress
      fi

      cd /var/www/wordpress
      if [ ! -f wp-config.php ]; then
        cp wp-config-sample.php wp-config.php
        sed -i "s/database_name_here/wordpress/" wp-config.php
        sed -i "s/username_here/wpuser/" wp-config.php
        sed -i "s/password_here/__WP_DB_PASS__/" wp-config.php
        for key in AUTH_KEY SECURE_AUTH_KEY LOGGED_IN_KEY NONCE_KEY AUTH_SALT SECURE_AUTH_SALT LOGGED_IN_SALT NONCE_SALT; do
          value="$(openssl rand -hex 32)"
          sed -i "0,/put your unique phrase here/s/put your unique phrase here/${value}/" wp-config.php
        done
      fi

      chown -R www-data:www-data /var/www/wordpress

      php_sock="$(find /run/php -maxdepth 1 -type s -name 'php*-fpm.sock' | sort | tail -n 1)"
      cat >/etc/nginx/sites-available/wordpress <<NGINX
      server {
          listen 80 default_server;
          listen [::]:80 default_server;
          server_name _;
          root /var/www/wordpress;
          index index.php index.html;

          client_max_body_size 64m;

          location / {
              try_files \$uri \$uri/ /index.php?\$args;
          }

          location ~ \.php$ {
              include snippets/fastcgi-php.conf;
              fastcgi_pass unix:${php_sock};
          }

          location ~ /\.ht {
              deny all;
          }
      }
      NGINX

      rm -f /etc/nginx/sites-enabled/default
      ln -sf /etc/nginx/sites-available/wordpress /etc/nginx/sites-enabled/wordpress
      nginx -t
      systemctl reload nginx

      if [ ! -x /usr/local/bin/wp ]; then
        curl -fsSL --retry 5 --retry-delay 5 \
          https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar \
          -o /usr/local/bin/wp
        chmod +x /usr/local/bin/wp
      fi

      export WP_CLI_CACHE_DIR=/tmp/wp-cli-cache
      install -d -m 0777 "$WP_CLI_CACHE_DIR"
      if ! sudo -u www-data -E wp core is-installed --path=/var/www/wordpress >/dev/null 2>&1; then
        sudo -u www-data -E wp core install \
          --path=/var/www/wordpress \
          --url="http://__VM_IP__" \
          --title="__WP_SITE_TITLE__" \
          --admin_user="__WP_ADMIN_USER__" \
          --admin_password="__WP_ADMIN_PASS__" \
          --admin_email="__WP_ADMIN_EMAIL__" \
          --skip-email
      fi

      touch /var/lib/cloud/instance/wordpress-ready

runcmd:
  - [ bash, /root/install-wordpress.sh ]
EOF_USER_DATA

  db_pass="$(openssl rand -hex 18)"
  sed -i \
    -e "s|__VM_HOSTNAME__|${VM_HOSTNAME}|g" \
    -e "s|__VM_IP__|${VM_IP}|g" \
    -e "s|__SSH_PUBKEY__|${SSH_PUBKEY}|g" \
    -e "s|__WP_DB_PASS__|${db_pass}|g" \
    -e "s|__WP_ADMIN_USER__|${WP_ADMIN_USER}|g" \
    -e "s|__WP_ADMIN_PASS__|${WP_ADMIN_PASS}|g" \
    -e "s|__WP_ADMIN_EMAIL__|${WP_ADMIN_EMAIL}|g" \
    -e "s|__WP_SITE_TITLE__|${WP_SITE_TITLE}|g" \
    "${workdir}/user-data"

  genisoimage -quiet -output "$SEED_ISO" -volid cidata -joliet -rock \
    "${workdir}/user-data" "${workdir}/meta-data"
  chown libvirt-qemu:kvm "$SEED_ISO"
  chmod 0600 "$SEED_ISO"

  virt-install \
    --name "$VM_NAME" \
    --memory "$VM_RAM_MB" \
    --vcpus "$VM_VCPUS" \
    --disk "path=${DISK_IMAGE},format=qcow2,bus=virtio" \
    --disk "path=${SEED_ISO},device=cdrom" \
    --os-variant ubuntu24.04 \
    --import \
    --network "network=default,mac=${VM_MAC},model=virtio" \
    --graphics none \
    --noautoconsole
else
  echo "Domain ${VM_NAME} already exists; leaving existing VM definition in place."
  virsh start "$VM_NAME" >/dev/null 2>&1 || true
fi

echo "Waiting for libvirt DHCP lease ${VM_IP}"
for _ in $(seq 1 120); do
  if virsh domifaddr "$VM_NAME" 2>/dev/null | grep -q "${VM_IP}/"; then
    break
  fi
  sleep 5
done

echo "Waiting for SSH on ${VM_IP}"
for _ in $(seq 1 120); do
  if ssh -i "$SSH_KEY" -o BatchMode=yes -o StrictHostKeyChecking=no \
    -o UserKnownHostsFile=/dev/null -o ConnectTimeout=5 \
    "pandalex@${VM_IP}" true >/dev/null 2>&1; then
    break
  fi
  sleep 5
done

echo "Waiting for cloud-init to finish"
ssh -i "$SSH_KEY" -o BatchMode=yes -o StrictHostKeyChecking=no \
  -o UserKnownHostsFile=/dev/null -o ConnectTimeout=10 \
  "pandalex@${VM_IP}" "sudo cloud-init status --wait" || true

echo "Checking services and WordPress endpoint"
ssh -i "$SSH_KEY" -o BatchMode=yes -o StrictHostKeyChecking=no \
  -o UserKnownHostsFile=/dev/null -o ConnectTimeout=10 \
  "pandalex@${VM_IP}" \
  "systemctl is-active nginx mysql; sudo test -f /var/lib/cloud/instance/wordpress-ready; curl -fsSI http://127.0.0.1/wp-login.php | head -n 1"

echo "VM_NAME=${VM_NAME}"
echo "VM_IP=${VM_IP}"
echo "SSH_KEY=${SSH_KEY}"
echo "WORDPRESS_URL=http://${VM_IP}/"
echo "WORDPRESS_LOGIN=http://${VM_IP}/wp-login.php"
