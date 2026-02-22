#!/bin/bash

echo "Starting Deployment..."

cd /var/www/pcvms

source venv/bin/activate

git pull origin main

pip install -r requirements.txt

python manage.py migrate --noinput

python manage.py collectstatic --noinput

sudo systemctl restart apache2

echo "Deployment Completed."
