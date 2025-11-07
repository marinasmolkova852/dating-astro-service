#!/bin/bash

# Загружаем переменные окружения из .env
set -a
source /.env
set +a

CONTAINER_NAME="project-mysql-1"
DATE=$(date +%F_%H-%M)
DB_NAME="${MYSQL_DATABASE}"
DB_USER="${MYSQL_USER}"
DB_PASSWORD="${MYSQL_PASSWORD}"
BACKUP_DIR="${BACKUP_DIR}"

echo "Backing up database '$DB_NAME' as user '$DB_USER'"
ы
# Создаём бэкап
docker exec $CONTAINER_NAME /usr/bin/mysqldump --no-tablespaces -u $DB_USER -p"$DB_PASSWORD" $DB_NAME > $BACKUP_DIR/backup_$DATE.sql

# Оставляем последние 7 дней
find $BACKUP_DIR -type f -name "*.sql" -mtime +7 -exec rm {} \;
