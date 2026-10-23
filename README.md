# Учёт оплат учебного центра

Мини-сервис: ученики, оплаты, список должников за месяц + мобильный веб-интерфейс.

**Стек:** Python 3.10+, FastAPI, SQLAlchemy 2.0, SQLite, Alembic, pytest · React, Vite, TypeScript, TanStack Query, Tailwind CSS, Framer Motion, Lucide.

## 1. Запуск с нуля

Структура: `backend/` — API (FastAPI), `frontend/` — интерфейс (React). Нужны Python 3.10+ и Node.js 18+.
Команды выполняются по одной, без `&&` — так они работают и в Windows PowerShell.

```
git clone <repo-url>
cd payments

# 1. фронтенд: сборка интерфейса
cd frontend
npm install
npm run build

# 2. бэкенд: зависимости, база данных, запуск
cd ../backend
python -m venv .venv
source .venv/bin/activate            # Linux/macOS
.venv\Scripts\Activate.ps1           # Windows PowerShell (вместо строки выше)
pip install -r requirements.txt
alembic upgrade head                 # создаёт app.db и таблицы
python -m app.seed                   # демо-данные (по желанию)
uvicorn app.main:app
```

Откройте http://127.0.0.1:8000 — интерфейс (удобен на телефоне), http://127.0.0.1:8000/docs — Swagger со всеми эндпоинтами.
Если PowerShell блокирует активацию `.venv`, один раз выполните `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

Режим разработки фронтенда: `uvicorn app.main:app` в папке `backend` и `npm run dev` в папке `frontend` (http://localhost:5173, запросы проксируются на бэкенд).
Тесты: в папке `backend` выполнить `pytest`. Другая БД: переменная `DATABASE_URL` (например, `postgresql+psycopg://user:pass@host/db`).

## 2. API

| Метод | URL | Что делает |
|---|---|---|
| POST | `/students` | создать ученика (`name`, `phone`, `group`, `monthly_amount`) |
| GET | `/students` | список (фильтр `?group=`) |
| GET / PATCH / DELETE | `/students/{id}` | получить / изменить (любые поля) / удалить |
| POST | `/students/{id}/payments` | добавить оплату (`amount`, `date`; без даты — сегодня) |
| GET | `/students/{id}/payments` | оплаты ученика, новые сверху |
| GET | `/debtors?month=YYYY-MM` | должники месяца (без `month` — текущий) |

Ответ `/debtors`: `{ month, total_debt, debtors: [{ student_id, name, phone, group, monthly_amount, paid, debt }] }`, по убыванию долга.

## 3. Допущения

- Долг = `monthly_amount − сумма оплат за месяц`; в список попадают ученики с долгом > 0, в том числе вообще без оплат.
- Месяц оплаты определяется по её `date`: `первое число месяца ≤ date < первое число следующего`. Границы (31-е / 1-е, декабрь / январь) покрыты тестами.
- Переплата на следующий месяц не переносится, старые долги не накапливаются — каждый месяц считается отдельно.
- Ученик, добавленный в середине месяца, должен полную сумму (без пропорционального расчёта).
- Деньги хранятся целыми числами в единицах валюты, без float.
- Удаление ученика каскадно удаляет его оплаты.
- Ошибки: неверный `month` или сумма ≤ 0 — 422; несуществующий ученик — 404.

## 4. Что улучшил бы за ещё одну неделю

1. Экран управления учениками в интерфейсе (сейчас ученики создаются через `/docs` или `app.seed`), а также редактирование и удаление оплат.
2. Авторизация (роли администратор / преподаватель): сейчас API открыт.
3. Перенос переплаты и накопительный долг между месяцами, расчёт пропорционально дате начала занятий.
4. PostgreSQL + Docker Compose для запуска одной командой, пагинация списков, CI с тестами и линтерами.
5. E2E-тесты интерфейса (Playwright) и уведомления должникам (Telegram / SMS).
