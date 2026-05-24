# TESDA PCVMS Production Deployment Guide

This guide deploys TESDA PCVMS on Ubuntu Server 22.04 using Gunicorn and either Nginx or Apache2 as the public web server.

The project is a Django 6 application, so use Python 3.12 or newer. Ubuntu 22.04 ships with Python 3.10 by default, which is not suitable for Django 6.

## 1. Deployment Overview

Recommended production stack:

- Ubuntu Server 22.04 LTS
- Python 3.12+
- Gunicorn application server
- PostgreSQL, MariaDB, or MySQL database
- Nginx or Apache2 reverse proxy
- Certbot for HTTPS
- Systemd for process management

Example values used in this guide:

```bash
APP_NAME=tesda_pcvms
APP_USER=pcvms
APP_DIR=/opt/tesda_pcvms
DOMAIN=pcvms.example.com
DB_NAME=tesda_pcvms
DB_USER=tesda_pcvms_user
DB_PASSWORD='CHANGE_THIS_STRONG_PASSWORD'
```

Replace these values with your real server details.

## 2. Prepare Ubuntu Server

Update the server:

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y software-properties-common curl git build-essential pkg-config \
    libpq-dev python3-dev python3-venv
```

Install Python 3.12:

```bash
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install -y python3.12 python3.12-venv python3.12-dev
python3.12 --version
```

Install WeasyPrint native dependencies for PDF support:

```bash
sudo apt install -y libpango-1.0-0 libpangoft2-1.0-0 libcairo2 libgdk-pixbuf-2.0-0 \
    libffi-dev shared-mime-info fonts-dejavu fonts-liberation
```

Create a dedicated Linux user:

```bash
sudo adduser --system --group --home /opt/tesda_pcvms pcvms
```

## 3. Upload or Clone the Project

Clone from Git:

```bash
sudo git clone https://github.com/YOUR_ORG/YOUR_REPO.git /opt/tesda_pcvms
sudo chown -R pcvms:pcvms /opt/tesda_pcvms
```

Or upload the project files to `/opt/tesda_pcvms`, then run:

```bash
sudo chown -R pcvms:pcvms /opt/tesda_pcvms
```

## 4. Create Python Virtual Environment

```bash
sudo -u pcvms python3.12 -m venv /opt/tesda_pcvms/venv
sudo -u pcvms /opt/tesda_pcvms/venv/bin/python -m pip install --upgrade pip wheel setuptools
sudo -u pcvms /opt/tesda_pcvms/venv/bin/pip install -r /opt/tesda_pcvms/requirements.txt
sudo -u pcvms /opt/tesda_pcvms/venv/bin/pip install gunicorn
```

If using MariaDB or MySQL, also install the MySQL driver:

```bash
sudo apt install -y default-libmysqlclient-dev
sudo -u pcvms /opt/tesda_pcvms/venv/bin/pip install mysqlclient
```

## 5. Choose and Configure Database

Choose only one database option.

### Option A: PostgreSQL

Install PostgreSQL:

```bash
sudo apt install -y postgresql postgresql-contrib
sudo systemctl enable --now postgresql
```

Create database and user:

```bash
sudo -u postgres psql
```

Inside the PostgreSQL shell:

```sql
CREATE DATABASE tesda_pcvms;
CREATE USER tesda_pcvms_user WITH PASSWORD 'CHANGE_THIS_STRONG_PASSWORD';
ALTER ROLE tesda_pcvms_user SET client_encoding TO 'utf8';
ALTER ROLE tesda_pcvms_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE tesda_pcvms_user SET timezone TO 'Asia/Manila';
GRANT ALL PRIVILEGES ON DATABASE tesda_pcvms TO tesda_pcvms_user;
\q
```

Production `DATABASE_URL`:

```env
DATABASE_URL=postgres://tesda_pcvms_user:CHANGE_THIS_STRONG_PASSWORD@127.0.0.1:5432/tesda_pcvms
```

### Option B: MariaDB

Install MariaDB:

```bash
sudo apt install -y mariadb-server mariadb-client default-libmysqlclient-dev
sudo systemctl enable --now mariadb
sudo mysql_secure_installation
```

Create database and user:

```bash
sudo mysql
```

Inside MariaDB:

```sql
CREATE DATABASE tesda_pcvms CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'tesda_pcvms_user'@'localhost' IDENTIFIED BY 'CHANGE_THIS_STRONG_PASSWORD';
GRANT ALL PRIVILEGES ON tesda_pcvms.* TO 'tesda_pcvms_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

Production `DATABASE_URL`:

```env
DATABASE_URL=mysql://tesda_pcvms_user:CHANGE_THIS_STRONG_PASSWORD@127.0.0.1:3306/tesda_pcvms
```

### Option C: MySQL

Install MySQL:

```bash
sudo apt install -y mysql-server mysql-client default-libmysqlclient-dev
sudo systemctl enable --now mysql
sudo mysql_secure_installation
```

Create database and user:

```bash
sudo mysql
```

Inside MySQL:

```sql
CREATE DATABASE tesda_pcvms CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'tesda_pcvms_user'@'localhost' IDENTIFIED BY 'CHANGE_THIS_STRONG_PASSWORD';
GRANT ALL PRIVILEGES ON tesda_pcvms.* TO 'tesda_pcvms_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

Production `DATABASE_URL`:

```env
DATABASE_URL=mysql://tesda_pcvms_user:CHANGE_THIS_STRONG_PASSWORD@127.0.0.1:3306/tesda_pcvms
```

## 6. Configure Production Environment

Create the production `.env`:

```bash
sudo -u pcvms nano /opt/tesda_pcvms/.env
```

Example `.env`:

```env
DJANGO_ENV=production

SECRET_KEY=CHANGE_THIS_TO_A_LONG_RANDOM_SECRET_KEY
DEBUG=False

ALLOWED_HOSTS=pcvms.example.com,127.0.0.1,localhost
CSRF_TRUSTED_ORIGINS=https://pcvms.example.com

DATABASE_URL=postgres://tesda_pcvms_user:CHANGE_THIS_STRONG_PASSWORD@127.0.0.1:5432/tesda_pcvms
DB_CONN_MAX_AGE=60

LANGUAGE_CODE=en-us
TIME_ZONE=Asia/Manila
USE_TZ=True

EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=no-reply@example.com
EMAIL_HOST_PASSWORD=CHANGE_THIS_EMAIL_PASSWORD
DEFAULT_FROM_EMAIL=TESDA PCVMS <no-reply@example.com>
SERVER_EMAIL=TESDA PCVMS <no-reply@example.com>

WEASYPRINT_ENABLED=True

SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_SSL_REDIRECT=True
USE_X_FORWARDED_PROTO=True

SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=False

LOG_LEVEL=INFO
```

Generate a strong Django secret key:

```bash
sudo -u pcvms /opt/tesda_pcvms/venv/bin/python - <<'PY'
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
PY
```

Secure the environment file:

```bash
sudo chmod 600 /opt/tesda_pcvms/.env
sudo chown pcvms:pcvms /opt/tesda_pcvms/.env
```

## 7. Prepare Django Application

Run Django checks:

```bash
cd /opt/tesda_pcvms
sudo -u pcvms DJANGO_ENV=production venv/bin/python manage.py check --deploy
```

Run migrations:

```bash
cd /opt/tesda_pcvms
sudo -u pcvms DJANGO_ENV=production venv/bin/python manage.py migrate
```

Collect static files:

```bash
cd /opt/tesda_pcvms
sudo -u pcvms DJANGO_ENV=production venv/bin/python manage.py collectstatic --noinput
```

Create an admin account:

```bash
cd /opt/tesda_pcvms
sudo -u pcvms DJANGO_ENV=production venv/bin/python manage.py createsuperuser
```

Create media directory:

```bash
sudo mkdir -p /opt/tesda_pcvms/media
sudo chown -R pcvms:www-data /opt/tesda_pcvms/media /opt/tesda_pcvms/staticfiles
sudo chmod -R 750 /opt/tesda_pcvms/media /opt/tesda_pcvms/staticfiles
```

Test Gunicorn manually:

```bash
cd /opt/tesda_pcvms
sudo -u pcvms DJANGO_ENV=production venv/bin/gunicorn config.wsgi:application \
    --bind 127.0.0.1:8001 \
    --workers 3
```

Open another terminal and test:

```bash
curl -I http://127.0.0.1:8001/
```

Stop the manual Gunicorn process with `CTRL+C`.

## 8. Configure Gunicorn Systemd Service

Create the service:

```bash
sudo nano /etc/systemd/system/tesda_pcvms.service
```

Paste:

```ini
[Unit]
Description=TESDA PCVMS Gunicorn Service
After=network.target

[Service]
User=pcvms
Group=www-data
WorkingDirectory=/opt/tesda_pcvms
Environment="DJANGO_ENV=production"
ExecStart=/opt/tesda_pcvms/venv/bin/gunicorn config.wsgi:application \
    --workers 3 \
    --bind unix:/run/tesda_pcvms.sock \
    --access-logfile - \
    --error-logfile -

RuntimeDirectory=tesda_pcvms
RuntimeDirectoryMode=0755
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now tesda_pcvms
sudo systemctl status tesda_pcvms
```

View logs:

```bash
sudo journalctl -u tesda_pcvms -f
```

## 9. Choose Web Server

Choose Nginx or Apache2.

## 10. Option A: Nginx Reverse Proxy

Install Nginx:

```bash
sudo apt install -y nginx
sudo systemctl enable --now nginx
```

Create site config:

```bash
sudo nano /etc/nginx/sites-available/tesda_pcvms
```

Paste:

```nginx
server {
    listen 80;
    server_name pcvms.example.com;

    client_max_body_size 25M;

    location /static/ {
        alias /opt/tesda_pcvms/staticfiles/;
        expires 30d;
        add_header Cache-Control "public";
    }

    location /media/ {
        alias /opt/tesda_pcvms/media/;
    }

    location / {
        proxy_pass http://unix:/run/tesda_pcvms.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/tesda_pcvms /etc/nginx/sites-enabled/tesda_pcvms
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

Allow firewall traffic:

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
sudo ufw status
```

Install HTTPS certificate:

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d pcvms.example.com
sudo systemctl reload nginx
```

## 11. Option B: Apache2 Reverse Proxy

Install Apache2:

```bash
sudo apt install -y apache2
sudo a2enmod proxy proxy_http proxy_uwsgi headers rewrite ssl
sudo systemctl enable --now apache2
```

Gunicorn is using a Unix socket. Apache proxy support for Unix sockets is available through `proxy_http`.

Create site config:

```bash
sudo nano /etc/apache2/sites-available/tesda_pcvms.conf
```

Paste:

```apache
<VirtualHost *:80>
    ServerName pcvms.example.com

    ErrorLog ${APACHE_LOG_DIR}/tesda_pcvms_error.log
    CustomLog ${APACHE_LOG_DIR}/tesda_pcvms_access.log combined

    Alias /static/ /opt/tesda_pcvms/staticfiles/
    <Directory /opt/tesda_pcvms/staticfiles/>
        Require all granted
    </Directory>

    Alias /media/ /opt/tesda_pcvms/media/
    <Directory /opt/tesda_pcvms/media/>
        Require all granted
    </Directory>

    ProxyPreserveHost On
    RequestHeader set X-Forwarded-Proto "http"
    ProxyPass /static/ !
    ProxyPass /media/ !
    ProxyPass / unix:/run/tesda_pcvms.sock|http://localhost/
    ProxyPassReverse / unix:/run/tesda_pcvms.sock|http://localhost/
</VirtualHost>
```

Enable site:

```bash
sudo a2ensite tesda_pcvms.conf
sudo a2dissite 000-default.conf
sudo apache2ctl configtest
sudo systemctl reload apache2
```

Allow firewall traffic:

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Apache Full'
sudo ufw enable
sudo ufw status
```

Install HTTPS certificate:

```bash
sudo apt install -y certbot python3-certbot-apache
sudo certbot --apache -d pcvms.example.com
sudo systemctl reload apache2
```

After Certbot creates HTTPS configuration, make sure HTTPS requests still pass the protocol header. In the SSL virtual host, include:

```apache
RequestHeader set X-Forwarded-Proto "https"
```

## 12. DNS Setup

Create an `A` record:

```text
pcvms.example.com -> YOUR_SERVER_PUBLIC_IP
```

Wait for DNS propagation, then verify:

```bash
dig pcvms.example.com
curl -I http://pcvms.example.com
curl -I https://pcvms.example.com
```

## 13. Deployment Update Procedure

Use this procedure whenever deploying new code.

```bash
cd /opt/tesda_pcvms
sudo -u pcvms git pull
sudo -u pcvms venv/bin/pip install -r requirements.txt
sudo -u pcvms DJANGO_ENV=production venv/bin/python manage.py migrate
sudo -u pcvms DJANGO_ENV=production venv/bin/python manage.py collectstatic --noinput
sudo -u pcvms DJANGO_ENV=production venv/bin/python manage.py check --deploy
sudo systemctl restart tesda_pcvms
```

Reload web server:

For Nginx:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

For Apache2:

```bash
sudo apache2ctl configtest
sudo systemctl reload apache2
```

## 14. Backups

Create backup directory:

```bash
sudo mkdir -p /var/backups/tesda_pcvms
sudo chmod 700 /var/backups/tesda_pcvms
```

### PostgreSQL Backup

```bash
sudo -u postgres pg_dump tesda_pcvms > /var/backups/tesda_pcvms/tesda_pcvms_$(date +%F_%H%M).sql
sudo tar -czf /var/backups/tesda_pcvms/media_$(date +%F_%H%M).tar.gz -C /opt/tesda_pcvms media
```

Restore PostgreSQL:

```bash
sudo -u postgres psql tesda_pcvms < /var/backups/tesda_pcvms/BACKUP_FILE.sql
```

### MariaDB or MySQL Backup

```bash
mysqldump -u tesda_pcvms_user -p tesda_pcvms > /var/backups/tesda_pcvms/tesda_pcvms_$(date +%F_%H%M).sql
sudo tar -czf /var/backups/tesda_pcvms/media_$(date +%F_%H%M).tar.gz -C /opt/tesda_pcvms media
```

Restore MariaDB or MySQL:

```bash
mysql -u tesda_pcvms_user -p tesda_pcvms < /var/backups/tesda_pcvms/BACKUP_FILE.sql
```

Automated daily backup example:

```bash
sudo nano /usr/local/bin/backup_tesda_pcvms.sh
```

PostgreSQL script:

```bash
#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR=/var/backups/tesda_pcvms
APP_DIR=/opt/tesda_pcvms
STAMP=$(date +%F_%H%M)

mkdir -p "$BACKUP_DIR"
sudo -u postgres pg_dump tesda_pcvms > "$BACKUP_DIR/db_$STAMP.sql"
tar -czf "$BACKUP_DIR/media_$STAMP.tar.gz" -C "$APP_DIR" media
find "$BACKUP_DIR" -type f -mtime +14 -delete
```

MariaDB/MySQL script:

```bash
#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR=/var/backups/tesda_pcvms
APP_DIR=/opt/tesda_pcvms
STAMP=$(date +%F_%H%M)

mkdir -p "$BACKUP_DIR"
mysqldump -u tesda_pcvms_user -p'CHANGE_THIS_STRONG_PASSWORD' tesda_pcvms > "$BACKUP_DIR/db_$STAMP.sql"
tar -czf "$BACKUP_DIR/media_$STAMP.tar.gz" -C "$APP_DIR" media
find "$BACKUP_DIR" -type f -mtime +14 -delete
```

Enable script:

```bash
sudo chmod 700 /usr/local/bin/backup_tesda_pcvms.sh
sudo crontab -e
```

Add:

```cron
0 2 * * * /usr/local/bin/backup_tesda_pcvms.sh
```

## 15. Logs and Troubleshooting

Gunicorn logs:

```bash
sudo journalctl -u tesda_pcvms -f
sudo systemctl status tesda_pcvms
```

Nginx logs:

```bash
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

Apache logs:

```bash
sudo tail -f /var/log/apache2/tesda_pcvms_access.log
sudo tail -f /var/log/apache2/tesda_pcvms_error.log
```

Check Django configuration:

```bash
cd /opt/tesda_pcvms
sudo -u pcvms DJANGO_ENV=production venv/bin/python manage.py check --deploy
```

Check database connection:

```bash
cd /opt/tesda_pcvms
sudo -u pcvms DJANGO_ENV=production venv/bin/python manage.py showmigrations
```

Restart services:

```bash
sudo systemctl restart tesda_pcvms
sudo systemctl reload nginx
```

For Apache:

```bash
sudo systemctl restart tesda_pcvms
sudo systemctl reload apache2
```

Common problems:

- `502 Bad Gateway`: Gunicorn is not running or socket permissions are wrong. Check `sudo journalctl -u tesda_pcvms -f`.
- Static files missing: run `collectstatic`, confirm `/opt/tesda_pcvms/staticfiles` exists, then reload web server.
- CSRF error after login: confirm `CSRF_TRUSTED_ORIGINS=https://your-domain` and `USE_X_FORWARDED_PROTO=True`.
- Redirect loop on HTTPS: confirm proxy sends `X-Forwarded-Proto` and `.env` has `USE_X_FORWARDED_PROTO=True`.
- MySQL/MariaDB install error: install `default-libmysqlclient-dev`, then reinstall `mysqlclient`.
- PDF generation fails: install WeasyPrint native packages and set `WEASYPRINT_ENABLED=True`.

## 16. Security Checklist

Before going live:

```bash
cd /opt/tesda_pcvms
sudo -u pcvms DJANGO_ENV=production venv/bin/python manage.py check --deploy
```

Confirm:

- `DEBUG=False`
- `DJANGO_ENV=production`
- Strong `SECRET_KEY`
- Real domain in `ALLOWED_HOSTS`
- HTTPS enabled
- `SESSION_COOKIE_SECURE=True`
- `CSRF_COOKIE_SECURE=True`
- Database password is strong
- `.env` permissions are `600`
- Regular database and media backups are configured
- Server firewall only allows SSH, HTTP, and HTTPS
- Admin account uses a strong password

## 17. Production Smoke Test

After deployment:

```bash
curl -I https://pcvms.example.com
```

Then test in the browser:

- Login page loads.
- Admin login works.
- Staff dashboard loads.
- Custodian dashboard loads.
- Static CSS and icons load correctly.
- File upload/media access works where applicable.
- PDF/export functions work.
- Email sending works if SMTP is configured.

