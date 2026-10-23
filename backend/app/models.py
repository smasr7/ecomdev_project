from datetime import date as Date

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    phone: Mapped[str] = mapped_column(String(32))
    group: Mapped[str] = mapped_column("group_name", String(80))  # group — зарезервированное слово SQL
    monthly_amount: Mapped[int]  # целые единицы валюты, без float
    payments: Mapped[list["Payment"]] = relationship(
        back_populates="student", cascade="all, delete-orphan"
    )


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), index=True)
    amount: Mapped[int]
    date: Mapped[Date] = mapped_column(index=True)
    student: Mapped[Student] = relationship(back_populates="payments")
