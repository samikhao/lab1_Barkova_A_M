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

# Настройка окружения
```bash
cp .env.example .env
```
Установить PostgreSQL и создать базу данных. Указать в .env ссылку вида:
```python
DATABASE_URL = "postgresql+psycopg://username:password@localhost:5432/db_name"
```
Заполнить .env своими данными.

# Создание таблиц и наполнение их данными для примера:
```bash
alembic upgrade head
```

# Запуск
```bash
uvicorn app.api.main:app --reload
```

# ERD
```mermaid
erDiagram
  users ||--o{ news : has
  users ||--o{ comments : has
  news  ||--o{ comments : has

  users {
    int id
    string name
    string email
    datetime registered_at
    boolean is_verified
    string avatar_url
  }

  news {
    int id
    string title
    string content
    datetime published_at
    string cover_url
    int author_id
  }

  comments {
    int id
    string text
    datetime published_at
    int news_id
    int author_id
  }
```

# Примеры работы всех эндпоинтов:
## 1. Проверка закрытых эндпоинтов
```bash
curl -i http://127.0.0.1:8000/api/v1/news/
```

Ответ сервера:
```json
{"detail":"Missing bearer token"}
```

## 2. Регистрация пользователя
```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Jack","email":"jack@example.com","password":"123456"}' | jq .
```

Ответ сервера:
```json
{
  "access": "<ACCESS_TOKEN>",
  "refresh": "<REFRESH_TOKEN>"
}
```

## 3. Логин
```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"jack@example.com","password":"123456"}' | jq .
```

Ответ сервера:
```json
{
  "access": "<ACCESS_TOKEN>",
  "refresh": "<REFRESH_TOKEN>"
}
```

## 4. Обновление токена
```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d "{\"refresh\":\"<REFRESH_TOKEN>\"}" | jq .
```

Ответ сервера:
```json
{
  "access": "<ACCESS_TOKEN>",
  "refresh": "<REFRESH_TOKEN>"
}
```

## 5. Logout
```bash
curl -i -X POST http://127.0.0.1:8000/api/v1/auth/logout \
  -H "Content-Type: application/json" \
  -d "{\"refresh\":\"<REFRESH_TOKEN>\"}"

```

## 6. Мои сессии
```bash
curl -s http://127.0.0.1:8000/api/v1/auth/sessions \
  -H "Authorization: Bearer <ACCESS_TOKEN>" | jq .

```

Ответ сервера:
```json
{
  "id": 15,
  "user_agent": "curl/8.7.1",
  "ip": "127.0.0.1",
  "created_at": "2025-10-17T14:26:04.072362+03:00",
  "expires_at": "2025-10-31T14:26:04.072336+03:00",
  "revoked": false
}
```

## 7. GitHub OAuth
Перейти по ссылке:
[GitHub Login](http://localhost:8000/api/v1/auth/github/login)
Авторизоваться через GitHub.
После редиректа получить JSON с токенами:
```json
{
  "access": "<ACCESS_TOKEN>",
  "refresh": "<REFRESH_TOKEN>"
}
```

## 8. Список пользователей
```bash
curl -s http://127.0.0.1:8000/api/v1/users/ \
  -H "Authorization: Bearer <ACCESS_TOKEN>" | jq .
```

Ответ сервера:
```json
[
  {
    "name": "Alice",
    "email": "alice@example.com",
    "avatar_url": null,
    "id": 1,
    "registered_at": "2025-10-16T21:38:08.546018+03:00",
    "is_verified_author": false
  },
  {
    "name": "Bob",
    "email": "bob@example.com",
    "avatar_url": null,
    "id": 2,
    "registered_at": "2025-10-16T21:38:08.546018+03:00",
    "is_verified_author": false
  },
  {
    "name": "Eve",
    "email": "eve@example.com",
    "avatar_url": null,
    "id": 3,
    "registered_at": "2025-10-16T21:38:08.546018+03:00",
    "is_verified_author": false
  },
  {
    "name": "Jack",
    "email": "jack@example.com",
    "avatar_url": null,
    "id": 4,
    "registered_at": "2025-10-17T14:11:04.318659+03:00",
    "is_verified_author": false
  }
]
```

## 9. Верификация пользователей админом
```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/users/1/verify \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"is_verified_author": true}' | jq .
```

Ответ сервера:
```json
{
  "name": "Alice",
  "email": "alice@example.com",
  "avatar_url": null,
  "id": 1,
  "registered_at": "2025-10-16T21:38:08.546018+03:00",
  "is_verified_author": false
}
```

## 10. Список новостей
```bash
curl -s http://127.0.0.1:8000/api/v1/news/ \
  -H "Authorization: Bearer <ACCESS_TOKEN>" | jq .
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
    }
  }
]
```

## 11. Создание новости
```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/news/ \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"title":"First post","content":{"text":"hello"},"cover_url":null}' | jq .
```

Ответ сервера:
```json
{
  "title": "First post",
  "content": {
    "text": "hello"
  },
  "cover_url": null,
  "id": 4,
  "published_at": "2025-10-17T14:34:15.663132+03:00",
  "author_id": 6
}
```

## 12. Редактирование своей новости
```bash
curl -s -X PATCH http://127.0.0.1:8000/api/v1/news/4 \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"title":"Updated title"}' | jq .
```

Ответ сервера:
```json
{
  "title": "Updated title",
  "content": {
    "text": "hello"
  },
  "cover_url": null,
  "id": 4,
  "published_at": "2025-10-17T14:34:15.663132+03:00",
  "author_id": 6
}
```

## 13. Удаление новости
```bash
curl -i -X DELETE http://127.0.0.1:8000/api/v1/news/1 \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

## 14. Список комментариев
```bash
curl -s http://127.0.0.1:8000/api/v1/comments/ \
  -H "Authorization: Bearer <ACCESS_TOKEN>" | jq .
```

Ответ сервера:
```json
[
  {
    "text": "seed comment 1",
    "id": 1,
    "published_at": "2025-10-16T21:38:08.546018+03:00",
    "news_id": 1,
    "author_id": 3
  },
  {
    "text": "seed comment 2",
    "id": 2,
    "published_at": "2025-10-16T21:38:08.546018+03:00",
    "news_id": 2,
    "author_id": 1
  }
]
```

## 15. Создание комментария
```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/comments/ \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"text":"nice post!","news_id":1}' | jq .
```

Ответ сервера:
```json
{
  "text": "nice post!",
  "id": 8,
  "published_at": "2025-10-17T14:34:15.664481+03:00",
  "news_id": 1,
  "author_id": 6
}
```

## 16. Редактирование комментария
```bash
curl -s -X PATCH http://127.0.0.1:8000/api/v1/comments/8 \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"text":"edited comment"}' | jq .
```

Ответ сервера:
```json
{
  "text": "edited comment",
  "id": 8,
  "published_at": "2025-10-17T14:34:15.664481+03:00",
  "news_id": 1,
  "author_id": 6
}
```
