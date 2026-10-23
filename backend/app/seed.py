"""Демо-данные: python -m app.seed"""
from datetime import date

from . import models as m
from .database import SessionLocal


def run() -> None:
    with SessionLocal() as db:
        if db.query(m.Student).first():
            print("В базе уже есть данные — пропускаю")
            return
        today = date.today()
        rows = [
            ("Алия Каримова", "+998901112233", "English A2", 600000, [350000]),
            ("Тимур Исмаилов", "+998935556677", "English A2", 600000, []),
            ("Мадина Рашидова", "+998977778899", "Математика 9", 450000, [450000]),
            ("Жасур Абдуллаев", "+998909990011", "Математика 9", 450000, [200000, 100000]),
            ("Севара Хамидова", "+998946665544", "IELTS", 900000, [1000000]),
        ]
        for name, phone, group, amount, pays in rows:
            student = m.Student(name=name, phone=phone, group=group, monthly_amount=amount)
            student.payments = [m.Payment(amount=a, date=today) for a in pays]
            db.add(student)
        db.commit()
        print(f"Добавлено учеников: {len(rows)}")


if __name__ == "__main__":
    run()
