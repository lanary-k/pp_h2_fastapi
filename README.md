# URL Shortener

Сервис для создания коротких ссылок.

## API

- `POST /links/shorten` — создать короткую ссылку.
- `GET /links/{short_code}` — перейти по короткой ссылке.
- `PUT /links/{short_code}` — изменить ссылку.
- `DELETE /links/{short_code}` — удалить ссылку.
- `GET /links/{short_code}/stats` — получить статистику.
- `GET /links/search` — найти ссылку по оригинальному URL.
- `POST /auth/register` — зарегистрировать пользователя.
- `POST /auth/jwt/login` — войти.

### Создание ссылки

```json
{
  "original_url": "https://example.com",
  "custom_alias": "example",
  "expires_at": "2026-09-20T15:30:00"
}
```

### Изменение ссылки

```json
{
  "original_url": "https://example.org"
}
```

## Запуск

Создать виртуальное окружение:

```bash
python -m venv .venv
source .venv/bin/activate
```

Установить зависимости:

```bash
pip install -r requirements.txt
```

Применить миграции:

```bash
alembic upgrade head
```

Запустить Redis.

Запустить приложение:

```bash
uvicorn main:app
```

Swagger:

`http://127.0.0.1:8000/docs`

## База данных

Для хранения данных используется PostgreSQL.

Основные таблицы:

- `user` — пользователи;
- `role` — роли;
- `link` — короткие ссылки.

В таблице `link` хранятся оригинальный URL, короткий код, количество переходов, даты создания и последнего использования, срок действия и пользователь, создавший ссылку.

Для кэширования используется Redis.