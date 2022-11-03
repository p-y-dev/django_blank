## Первоначальная настройка
- Установить в систему docker и docker-compose
  - [install Doker](https://docs.docker.com/engine/install/ubuntu/)
  - [install compose](https://docs.docker.com/compose/install/linux/)
- В docker-compose.yml у всех контейнеров задать соответствующие название в container_name, исходя из названия проекта
- Так же нужно задать соответствующие имена для volumes
- В корне проекта создать файл .env, пример переменных среды окружения находиться в .env.example. Переменная DB_HOST должна соответствовать названию контейнера для базы данных.

## Поднятие проекта
#### Без плагина compose
```bash
docker-compose up --build
```

## Работа с manage.py
Работа с manage.py выполняется в контейнере app, командой:
```
docker-compose exec app ./manage.py название_команды
```

При создании миграций или приложений джанго в контейнере, они будут пробрасываться на локальную машину, 
но с правами пользователя контейнера, поэтому для работы с этими файлами/директориями нужно на локальной машине выполнить:
```bash
sudo chown -R $USER:$USER файл/директория
```

## Работа с контейнерами
#### Вход в контейнер
```bash
docker exec -it название_контейнера bash
```
#### Просмотр логов
```bash
docker logs -f название_контейнера
```

