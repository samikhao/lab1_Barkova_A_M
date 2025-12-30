# Структура взаимодействия с БД и Redis

**Postgres:**

- `users` — профиль пользователя (имя, email, флаги `is_admin`, `is_verified_author`, аватар и т.д.).
- `news` — новости (`title`, `content`, `cover`, `author_id`, `published_at`).
- `comments` — комментарии (`content`, `news_id`, `author_id`, `created_at`, `updated_at`).
- _(Таблица `refresh_sessions` сохранена для совместимости.)_

**Redis:**

- **Сессии:** `app:session:<sha256(refresh)>` -> JSON `{ user_id, user_agent, ip, created_at, expires_at }`  
  TTL = `REFRESH_TTL_DAYS * 86400` (совпадает со сроком жизни refresh-токена).
- **Новости (warm-cache):**
  - список: `app:news:all` -> JSON-массив новостей, TTL = 300 сек
- **Пользователь (роли):** `app:user:<id>` -> `{ id, is_admin, is_verified_author }`, TTL = 300 сек

---

## Потоки запросов

**Новости (`GET /api/v1/news`):**

1. `GET` -> Redis `app:news:all`
   - есть ключ -> **HIT** -> отдать из Redis
   - нет ключа -> **MISS** -> прочитать из Postgres -> `SETEX` в Redis -> отдать ответ
2. Создание/изменение/удаление новости -> инвалидация:
   - `DEL app:news:all` (+ при необходимости `DEL app:news:id:<id>`)

**Аутентификация / сессии (`/auth/login`, `/auth/refresh`, `/auth/logout`):**

- **login:** после выдачи refresh -> `SETEX app:session:<hash>` (TTL = срок refresh)
- **refresh:**
  - `HIT` по `app:session:<hash>` -> проверка срока -> `DEL старый` -> `SETEX новый`
  - `MISS` -> `401 Refresh session not found or revoked`
- **logout:** `DEL app:session:<hash>`

**Роли пользователя (быстрые проверки):**

- `get_user_roles_fast(user_id)`
  - Redis `app:user:<id>`: **HIT** -> отдать роли
  - **MISS** -> Postgres -> собрать `{id, is_admin, is_verified_author}` -> `SETEX` -> отдать роли
- При изменении ролей (`POST /users/{id}/verify`) -> `DEL app:user:<id>`

---

## Логирование

Во всех критичных точках пишем источник данных:

- **Новости:**  
  `cache MISS|SET|HIT: app:news:all`  
  `cache DEL (create|update|delete): <id>`
- **Сессии:**  
  `session SET|HIT|DEL: app:session:<hash>`
- **Пользователь (роли):**  
  `user cache MISS|SET|HIT|DEL: app:user:<id>`
