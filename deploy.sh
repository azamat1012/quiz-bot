#!/bin/bash

set -e

PROJECT_DIR="/opt/quiz-bot"
VENV_PATH="/opt/quiz-bot/bin/env/activate"
TG_BOT_SERVICE="telegram-quiz-bot.service"
VK_BOT_SERVICE="vk-quiz-bot.service"
echo "-------НАЧАЛА ДЕПЛОЯ------"


echo "---ЗАГРУЗКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ"
cd  $PROJECT_DIR
source .env

LATEST_COMMIT=$(git rev-parse HEAD)
echo "LATEST COMMIT $LATEST_COMMIT"

echo "------UPDATE THE CODE FROM REPO-------"
git pull

echo "-----DOWNLOAD THE PYTHON DEPENDENCIESES------"
source $VENV_PATH
pip install -r requirements.txt

echo "----RESTARTING SERVICES-----"
sudo systemctl daemon-reload
sudo systemctl restart $TG_BOT_SERVICE
sudo systemctl restart $VK_BOT_SERVICE

echo "--------DEPLOY IS COMPLETED----------"

