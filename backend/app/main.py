from datetime import date
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from . import models as m
from . import schemas as s
from .database import get_db

app = FastAPI(title="Учёт оплат учебного центра")

MONTH_PATTERN = r"^(19|20)\d{2}-(0[1-9]|1[0-2])$"


def get_student(db: Session, student_id: int) -> m.Student:
    student = db.get(m.Student, student_id)
    if student is None:
        raise HTTPException(404, "Ученик не найден")
    return student


# ---------- Ученики ----------
@app.post("/students", response_model=s.StudentOut, status_code=201)
def create_student(data: s.StudentIn, db: Session = Depends(get_db)):
    student = m.Student(**data.model_dump())
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


@app.get("/students", response_model=list[s.StudentOut])
def list_students(group: str | None = None, db: Session = Depends(get_db)):
    query = select(m.Student).order_by(m.Student.name)
    if group:
        query = query.where(m.Student.group == group)
    return db.scalars(query).all()


@app.get("/students/{student_id}", response_model=s.StudentOut)
def read_student(student_id: int, db: Session = Depends(get_db)):
    return get_student(db, student_id)


@app.patch("/students/{student_id}", response_model=s.StudentOut)
def update_student(student_id: int, data: s.StudentPatch, db: Session = Depends(get_db)):
    student = get_student(db, student_id)
    for key, value in data.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(student, key, value)
    db.commit()
    db.refresh(student)
    return student


@app.delete("/students/{student_id}", status_code=204)
def delete_student(student_id: int, db: Session = Depends(get_db)):
    db.delete(get_student(db, student_id))  # платежи удаляются каскадом
    db.commit()


# ---------- Оплаты ----------
@app.post("/students/{student_id}/payments", response_model=s.PaymentOut, status_code=201)
def add_payment(student_id: int, data: s.PaymentIn, db: Session = Depends(get_db)):
    get_student(db, student_id)
    payment = m.Payment(student_id=student_id, amount=data.amount, date=data.date or date.today())
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


@app.get("/students/{student_id}/payments", response_model=list[s.PaymentOut])
def list_payments(student_id: int, db: Session = Depends(get_db)):
    get_student(db, student_id)
    query = (
        select(m.Payment)
        .where(m.Payment.student_id == student_id)
        .order_by(m.Payment.date.desc(), m.Payment.id.desc())
    )
    return db.scalars(query).all()


# ---------- Должники ----------
@app.get("/debtors", response_model=s.DebtorsOut)
def debtors(
    month: str | None = Query(None, pattern=MONTH_PATTERN, description="YYYY-MM, по умолчанию текущий"),
    db: Session = Depends(get_db),
):
    month = month or date.today().strftime("%Y-%m")
    year, mon = map(int, month.split("-"))
    start = date(year, mon, 1)
    end = date(year + (mon == 12), mon % 12 + 1, 1)  # первый день следующего месяца

    paid = func.coalesce(func.sum(m.Payment.amount), 0)
    rows = db.execute(
        select(m.Student, paid)
        .outerjoin(
            m.Payment,
            and_(m.Payment.student_id == m.Student.id, m.Payment.date >= start, m.Payment.date < end),
        )
        .group_by(m.Student.id)
        .having(paid < m.Student.monthly_amount)
    ).all()

    items = [
        s.Debtor(
            student_id=st.id, name=st.name, phone=st.phone, group=st.group,
            monthly_amount=st.monthly_amount, paid=int(p), debt=st.monthly_amount - int(p),
        )
        for st, p in rows
    ]
    items.sort(key=lambda d: (-d.debt, d.name))
    return s.DebtorsOut(month=month, total_debt=sum(d.debt for d in items), debtors=items)


# ---------- Интерфейс (собранный фронтенд, если есть) ----------
DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if DIST.is_dir():
    app.mount("/", StaticFiles(directory=DIST, html=True), name="ui")
