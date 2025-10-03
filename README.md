# Установка проекта
```bash
git clone https://github.com/itmo-webdev/lab1_Barkova_A_M.git
cd lab1_Barkova_A_M
```

# Создание виртуального окружения
```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

# Установка зависимостей
```bash
pip install -r requirements.txt
```

# Настройка базы данных
Установить PostgreSQL и создать базу данных. Указать в .env ссылку вида:
```python
DATABASE_URL = "postgresql+psycopg://username:password@localhost:5432/db_name"
```

# Создание таблиц и наполнение их данными для примера:
alembic upgrade head

# Запуск
uvicorn app.api.main:app --reload

# Примеры работы всех эндпоинтов:
1. Создание пользователя
```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/users/ \
  -H "Content-Type: application/json" \
  -d '{"name":"Sasha","email":"sasha@example.com","avatar_url":null}' | jq .
```
Ответ сервера:
```json
{
  "name": "Sasha",
  "email": "sasha@example.com",
  "avatar_url": null,
  "id": 4,
  "registered_at": "2025-10-03T13:40:20.640014+03:00",
  "is_verified": false
}
```

2. Получение списка пользователей
```bash
curl -s http://127.0.0.1:8000/api/v1/users/ | jq .
```
Ответ сервера:
```json
[
  {
    "name": "Alice",
    "email": "alice@example.com",
    "avatar_url": null,
    "id": 1,
    "registered_at": "2025-10-03T13:07:50.549712+03:00",
    "is_verified": false
  },
  {
    "name": "Bob",
    "email": "bob@example.com",
    "avatar_url": null,
    "id": 2,
    "registered_at": "2025-10-03T13:07:50.549712+03:00",
    "is_verified": false
  },
  {
    "name": "Eve",
    "email": "eve@example.com",
    "avatar_url": null,
    "id": 3,
    "registered_at": "2025-10-03T13:07:50.549712+03:00",
    "is_verified": false
  },
  {
    "name": "Sasha",
    "email": "sasha@example.com",
    "avatar_url": null,
    "id": 4,
    "registered_at": "2025-10-03T13:40:20.640014+03:00",
    "is_verified": false
  }
]
```

3. Верификация пользователя
```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/users/4/verify \
  -H "Content-Type: application/json" \
  -d '{"is_verified": true}' | jq .
```
Ответ сервера:
```json
{
  "name": "Sasha",
  "email": "sasha@example.com",
  "avatar_url": null,
  "id": 4,
  "registered_at": "2025-10-03T13:40:20.640014+03:00",
  "is_verified": true
}
```

4. Создание новости
```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/news/ \
  -H "Content-Type: application/json" \
  -d '{"title":"Первая новость","content":{"text":"hello, world"},"cover_url":null,"author_id":4}' | jq .
```
Ответ сервера:
```json
{
  "title": "Первая новость",
  "content": {
    "text": "hello, world"
  },
  "cover_url": null,
  "id": 3,
  "published_at": "2025-10-03T13:40:20.726784+03:00",
  "author_id": 4
}
```

5. Получение списка новостей
```bash
curl -s http://127.0.0.1:8000/api/v1/news/ | jq .
```
Ответ сервера:
```json
[
  {
    "title": "Alice first post",
    "content": {
      "blocks": [
        "seed post 1"
      ]
    },
    "cover_url": null,
    "id": 1,
    "published_at": "2025-10-03T13:07:50.549712+03:00",
    "author_id": 1
  },
  {
    "title": "Bob's update",
    "content": {
      "blocks": [
        "seed post 2"
      ]
    },
    "cover_url": null,
    "id": 2,
    "published_at": "2025-10-03T13:07:50.549712+03:00",
    "author_id": 2
  },
  {
    "title": "Первая новость",
    "content": {
      "text": "hello, world"
    },
    "cover_url": null,
    "id": 3,
    "published_at": "2025-10-03T13:40:20.726784+03:00",
    "author_id": 4
  }
]
```

6. Редактирование новости
```bash
curl -s -X PATCH http://127.0.0.1:8000/api/v1/news/3 \
  -H "Content-Type: application/json" \
  -d '{"title":"Первая новость — апдейт","content":{"text":"обновили текст"}}' | jq .
```
Ответ сервера:
```json
{
  "title": "Первая новость — апдейт",
  "content": {
    "text": "обновили текст"
  },
  "cover_url": null,
  "id": 3,
  "published_at": "2025-10-03T13:40:20.726784+03:00",
  "author_id": 4
}
```

7. Удаление новости
```bash
curl -i -X DELETE http://127.0.0.1:8000/api/v1/news/3
```
Ответ сервера:
```http
HTTP/1.1 204 No Content
date: Fri, 03 Oct 2025 10:51:45 GMT
server: uvicorn
content-type: application/json
```

8. Создание комментария
```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/comments/ \
  -H "Content-Type: application/json" \
  -d '{"text":"классная новость!","news_id":1,"author_id":1}' | jq .
```
Ответ сервера:
```json
{
  "text": "классная новость!",
  "id": 3,
  "published_at": "2025-10-03T13:40:20.728387+03:00",
  "news_id": 1,
  "author_id": 1
}
```

9. Получение списка комментариев
```bash
curl -s http://127.0.0.1:8000/api/v1/comments/ | jq .
```
Ответ сервера:
```json
[
  {
    "text": "seed comment 1",
    "id": 1,
    "published_at": "2025-10-03T13:07:50.549712+03:00",
    "news_id": 1,
    "author_id": 3
  },
  {
    "text": "seed comment 2",
    "id": 2,
    "published_at": "2025-10-03T13:07:50.549712+03:00",
    "news_id": 2,
    "author_id": 1
  },
  {
    "text": "классная новость!",
    "id": 3,
    "published_at": "2025-10-03T13:40:20.728387+03:00",
    "news_id": 1,
    "author_id": 1
  }
]
```

10. Редактирование комментария
```bash
curl -s -X PATCH http://127.0.0.1:8000/api/v1/comments/3 \
  -H "Content-Type: application/json" \
  -d '{"text":"исправил опечатку"}' | jq .
```
Ответ сервера:
```json
{
  "text": "исправил опечатку",
  "id": 3,
  "published_at": "2025-10-03T13:40:20.728387+03:00",
  "news_id": 1,
  "author_id": 1
}
```
