# Используем официальный Node.js образ
FROM node:23-slim

# Создаем рабочую директорию
WORKDIR /app

# Копируем package.json и package-lock.json (если есть)
COPY package*.json ./

# Устанавливаем зависимости
RUN npm install --verbose

# Копируем весь код в контейнер
COPY . .

# Экспонируем порт
EXPOSE 3000

# Запускаем приложение
CMD ["node", "server.js"]
