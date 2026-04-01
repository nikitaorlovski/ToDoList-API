# 📝 ToDoList API

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green.svg)](https://fastapi.tiangolo.com/)
[![codecov](https://codecov.io/gh/nikitaorlovski/ToDoList-API/branch/main/graph/badge.svg)](https://codecov.io/gh/nikitaorlovski/ToDoList-API)
[![Tests](https://github.com/nikitaorlovski/ToDoList-API/actions/workflows/test.yml/badge.svg)](https://github.com/nikitaorlovski/ToDoList-API/actions/workflows/test.yml)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Полноценное REST API для управления задачами (To-Do List), написанное на **FastAPI** с использованием **SQLAlchemy (async)**, **JWT-аутентификации** и **Poetry**.  
Проект покрыт тестами (pytest + httpx + pytest-asyncio), имеет CI-интеграцию с **GitHub Actions** и **Codecov**.

---

## 🚀 Возможности

- 🔐 Регистрация и вход пользователя с JWT-токенами (`access` + `refresh`)
- ✅ CRUD-операции над задачами:
  - создание / редактирование / удаление / просмотр
- 📄 Пагинация задач `/api/todos/{page}/{limit}`
- ⚙️ Асинхронная ORM — **SQLAlchemy 2.0 Async**
- 🧩 Pydantic-валидация данных
- 🧱 Слои приложения: API, Core, DB, Repositories
- 🧪 Полное покрытие тестами с отчётом Codecov

---

## 🧰 Технологии

| Компонент | Технология |
|------------|-------------|
| Backend | [FastAPI](https://fastapi.tiangolo.com/) |
| ORM | SQLAlchemy (async) |
| База данных | SQLite (для тестов), можно заменить на PostgreSQL |
| Тесты | pytest, pytest-asyncio, httpx |
| Авторизация | JWT (PyJWT, bcrypt) |
| Управление зависимостями | Poetry |
| CI/CD | GitHub Actions + Codecov |

---

## ⚙️ Установка и запуск

### 1. Клонируй репозиторий
```bash
git clone https://github.com/nikitaorlovski/ToDoList-API.git
cd ToDoList-API
```
### 2. Создание приватного ключа (private.pem)
```bash
openssl genpkey -algorithm RSA -out private.pem -aes256 -pkeyopt rsa_keygen_bits:2048
```

### 3. Извлечение публичного ключа (public.pem)
```bash
openssl rsa -pubout -in private.pem -out public.pem
```

### 4. Создайте файл .env с переменной:
```bash
ALGORITHM=RS256
```

### 5. Установите зависимости с помощью poetry
```bash
poetry install
```

### 6. Запустите приложение
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```
