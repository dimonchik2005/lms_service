# LMS Service

Backend-сервис для управления онлайн-обучением. Проект предоставляет REST API для работы с курсами, уроками, пользователями, подписками и платежами.

## Возможности проекта

* регистрация и управление пользователями;
* авторизация по JWT-токенам;
* CRUD для курсов через ViewSet;
* CRUD для уроков через Generic API Views;
* разграничение доступа между владельцами и модераторами;
* подписка на обновления курсов;
* проверка ссылок на видео — разрешён только YouTube;
* пагинация курсов и уроков;
* история и фильтрация платежей;
* создание оплаты курса через Stripe;
* Swagger и ReDoc документация;
* фоновые задачи через Celery;
* Redis в качестве брокера Celery;
* уведомление подписчиков об обновлении курса;
* блокировка пользователей, не входивших более 30 дней;
* периодический запуск задач через Celery Beat.

## Стек технологий

* Python 3.14
* Django 6
* Django REST Framework
* PostgreSQL
* Simple JWT
* django-filter
* drf-spectacular
* Stripe
* Celery
* Redis
* Docker
* Poetry

## Установка проекта

Клонируйте репозиторий:

```powershell
git clone https://github.com/dimonchik2005/lms_service.git
cd lms_service
```

Установите зависимости:

```powershell
poetry install
```

Активируйте виртуальное окружение:

```powershell
poetry env activate
```

Команда выведет путь к скрипту активации. Выполните показанную команду.

Также можно запускать команды без ручной активации:

```powershell
poetry run python manage.py check
```

## Переменные окружения

Создайте `.env` на основе `.env.example`:

```powershell
Copy-Item .env.example .env
```

Заполните необходимые значения в `.env`.

Пример основных переменных:

```dotenv
SECRET_KEY=your-django-secret-key
DEBUG=True

POSTGRES_DB=lms_service
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-database-password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

STRIPE_SECRET_KEY=sk_test_your-test-key
STRIPE_SUCCESS_URL=http://127.0.0.1:8000/api/payments/success/
STRIPE_CANCEL_URL=http://127.0.0.1:8000/api/payments/cancel/

CELERY_BROKER_URL=redis://127.0.0.1:6379/0
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/1

DEFAULT_FROM_EMAIL=lms-service@example.com
```

Настоящие пароли, `SECRET_KEY` и ключ Stripe нельзя добавлять в Git.

## База данных

Создайте и примените миграции:

```powershell
poetry run python manage.py makemigrations
poetry run python manage.py migrate
```

При необходимости создайте администратора:

```powershell
poetry run python manage.py createsuperuser
```

## Запуск Django

```powershell
poetry run python manage.py runserver
```

Сервер будет доступен по адресу:

```text
http://127.0.0.1:8000/
```

Административная панель:

```text
http://127.0.0.1:8000/admin/
```

## Документация API

OpenAPI-схема:

```text
http://127.0.0.1:8000/api/schema/
```

Swagger UI:

```text
http://127.0.0.1:8000/api/docs/
```

ReDoc:

```text
http://127.0.0.1:8000/api/redoc/
```

Проверка схемы:

```powershell
poetry run python manage.py spectacular --file schema.yml --validate
```

## Основные эндпоинты

### Авторизация

```text
POST /api/token/
POST /api/token/refresh/
```

### Пользователи

```text
GET    /api/users/
POST   /api/users/register/
GET    /api/users/{id}/
PUT    /api/users/{id}/
PATCH  /api/users/{id}/
DELETE /api/users/{id}/
```

### Курсы

```text
GET    /api/courses/
POST   /api/courses/
GET    /api/courses/{id}/
PUT    /api/courses/{id}/
PATCH  /api/courses/{id}/
DELETE /api/courses/{id}/
```

### Уроки

```text
GET    /api/lessons/
POST   /api/lessons/
GET    /api/lessons/{id}/
PUT    /api/lessons/{id}/
PATCH  /api/lessons/{id}/
DELETE /api/lessons/{id}/
```

### Подписки

```text
POST /api/subscriptions/toggle/
```

Пример запроса:

```json
{
  "course_id": 1
}
```

Если подписки нет, она создаётся. Если подписка уже существует, она удаляется.

### Платежи

```text
GET  /api/users/payments/
POST /api/users/payments/checkout/
GET  /api/users/payments/{id}/status/
```

Пример создания Stripe-платежа:

```json
{
  "paid_course": 1,
  "amount": "1000.00"
}
```

Ответ содержит идентификаторы Stripe и ссылку на страницу оплаты.

## JWT-авторизация

Получите токены:

```http
POST /api/token/
```

Тело запроса:

```json
{
  "email": "user@example.com",
  "password": "your-password"
}
```

Для защищённых эндпоинтов передавайте access-токен:

```text
Authorization: Bearer ACCESS_TOKEN
```

## Права доступа

Обычный пользователь:

* создаёт курсы и уроки;
* просматривает, изменяет и удаляет только свои материалы;
* управляет своими подписками;
* просматривает собственные платежи.

Модератор:

* просматривает любые курсы и уроки;
* редактирует любые курсы и уроки;
* не создаёт и не удаляет материалы.

Владелец назначается автоматически из текущего авторизованного пользователя.

## Stripe

Stripe используется в тестовом режиме.

При создании оплаты приложение:

1. создаёт локальную запись платежа;
2. создаёт продукт Stripe;
3. создаёт цену Stripe;
4. переводит сумму из рублей в копейки;
5. создаёт Checkout Session;
6. сохраняет Stripe ID и ссылку на оплату;
7. возвращает данные платежа пользователю.

Тестовый секретный ключ должен начинаться с:

```text
sk_test_
```

Настоящий Stripe-ключ должен храниться только в `.env`.

## Redis

Запустите Docker Desktop.

Создайте контейнер Redis:

```powershell
docker run -d --name lms-redis -p 6379:6379 redis:7-alpine
```

При последующих запусках используйте:

```powershell
docker start lms-redis
```

Проверка Redis:

```powershell
docker exec -it lms-redis redis-cli ping
```

Ожидаемый ответ:

```text
PONG
```

Остановка контейнера:

```powershell
docker stop lms-redis
```

## Celery

Celery использует Redis как брокер фоновых задач.

Запуск Worker на Windows:

```powershell
poetry run celery -A config worker --loglevel=INFO --pool=solo
```

Worker должен зарегистрировать задачи:

```text
lms.tasks.send_course_update_email
users.tasks.deactivate_inactive_users
```

Проверка зарегистрированных задач:

```powershell
poetry run celery -A config inspect registered
```

## Celery Beat

Запустите планировщик в отдельном терминале:

```powershell
poetry run celery -A config beat --loglevel=INFO
```

Celery Beat ежедневно запускает задачу проверки пользователей.

Пользователи, которые не входили более 30 дней, блокируются одним пакетным запросом:

```python
queryset.update(is_active=False)
```

Временная зона Celery совпадает с `TIME_ZONE` проекта.

## Уведомления об обновлении курса

После успешного обновления курса Celery отправляет уведомление всем активным пользователям, подписанным именно на этот курс.

Повторное уведомление запускается только в том случае, если с предыдущего обновления курса прошло не менее четырёх часов.

Задача ставится в очередь после успешного сохранения изменений в базе данных.

## Полный локальный запуск

Для полной работы проекта необходимо открыть четыре терминала.

Первый терминал — Django:

```powershell
poetry run python manage.py runserver
```

Второй терминал — Celery Worker:

```powershell
poetry run celery -A config worker --loglevel=INFO --pool=solo
```

Третий терминал — Celery Beat:

```powershell
poetry run celery -A config beat --loglevel=INFO
```

Redis работает в Docker:

```powershell
docker start lms-redis
```

## Тестирование

Запуск всех тестов:

```powershell
poetry run python manage.py test
```

Проверка покрытия:

```powershell
poetry run coverage run manage.py test
poetry run coverage report
```

Создание HTML-отчёта:

```powershell
poetry run coverage html
```

Отчёт будет создан в директории:

```text
htmlcov/
```

## Проверка проекта перед коммитом

```powershell
poetry run python manage.py check
poetry run python manage.py makemigrations --check
poetry run python manage.py test
poetry run python manage.py spectacular --file schema.yml --validate
git diff --check
git status
```

## Автор

GitHub: [dimonchik2005](https://github.com/dimonchik2005)
