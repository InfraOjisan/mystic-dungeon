#!/usr/bin/env bash
set -euo pipefail

VM_IP="192.168.122.50"
WP_ADMIN_USER="AdminPandalex"
WP_ADMIN_PASS="wpAdmin001Pass"
WP_ADMIN_EMAIL="admin@example.test"
WP_SITE_TITLE="lub_wp_test"
WP_PATH="/var/www/wordpress"

if [ "$(id -u)" -ne 0 ]; then
  echo "This script must run as root." >&2
  exit 1
fi

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y \
  ca-certificates curl nginx mysql-server \
  php-fpm php-mysql php-curl php-gd php-mbstring php-xml php-zip unzip

systemctl enable --now mysql
systemctl enable --now nginx

db_pass="$(openssl rand -hex 18)"
mysql <<SQL
CREATE DATABASE IF NOT EXISTS wordpress DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'wpuser'@'localhost' IDENTIFIED BY '${db_pass}';
ALTER USER 'wpuser'@'localhost' IDENTIFIED BY '${db_pass}';
GRANT ALL PRIVILEGES ON wordpress.* TO 'wpuser'@'localhost';
FLUSH PRIVILEGES;
SQL

install -d -m 0755 -o www-data -g www-data "$WP_PATH"
if [ ! -f "${WP_PATH}/wp-settings.php" ]; then
  curl -fsSL --retry 5 --retry-delay 5 https://wordpress.org/latest.tar.gz \
    | tar -xz --strip-components=1 -C "$WP_PATH"
fi

cd "$WP_PATH"
if [ ! -f wp-config.php ]; then
  cp wp-config-sample.php wp-config.php
fi

sed -i "s/database_name_here/wordpress/" wp-config.php
sed -i "s/username_here/wpuser/" wp-config.php
sed -i "s/password_here/${db_pass}/" wp-config.php
sed -i "s/define( *'DB_NAME'.*/define( 'DB_NAME', 'wordpress' );/" wp-config.php
sed -i "s/define( *'DB_USER'.*/define( 'DB_USER', 'wpuser' );/" wp-config.php
sed -i "s/define( *'DB_PASSWORD'.*/define( 'DB_PASSWORD', '${db_pass}' );/" wp-config.php

while grep -q "put your unique phrase here" wp-config.php; do
  value="$(openssl rand -hex 32)"
  sed -i "0,/put your unique phrase here/s/put your unique phrase here/${value}/" wp-config.php
done

chown -R www-data:www-data "$WP_PATH"

php_sock="$(find /run/php -maxdepth 1 -type s -name 'php*-fpm.sock' | sort | tail -n 1)"
cat >/etc/nginx/sites-available/wordpress <<NGINX
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;
    root ${WP_PATH};
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
if ! sudo -u www-data -E wp core is-installed --path="$WP_PATH" >/dev/null 2>&1; then
  sudo -u www-data -E wp core install \
    --path="$WP_PATH" \
    --url="http://${VM_IP}" \
    --title="$WP_SITE_TITLE" \
    --admin_user="$WP_ADMIN_USER" \
    --admin_password="$WP_ADMIN_PASS" \
    --admin_email="$WP_ADMIN_EMAIL" \
    --skip-email
else
  sudo -u www-data -E wp option update siteurl "http://${VM_IP}" --path="$WP_PATH"
  sudo -u www-data -E wp option update home "http://${VM_IP}" --path="$WP_PATH"
fi

touch /var/lib/cloud/instance/wordpress-ready
systemctl is-active nginx mysql
curl -fsSI "http://127.0.0.1/wp-login.php" | head -n 1
