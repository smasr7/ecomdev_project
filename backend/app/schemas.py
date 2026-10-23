from datetime import date as Date

from pydantic import BaseModel, ConfigDict, Field


class StudentIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    phone: str = Field(min_length=3, max_length=32)
    group: str = Field(min_length=1, max_length=80)
    monthly_amount: int = Field(gt=0)


class StudentPatch(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=120)
    phone: str | None = Field(None, min_length=3, max_length=32)
    group: str | None = Field(None, min_length=1, max_length=80)
    monthly_amount: int | None = Field(None, gt=0)


class StudentOut(StudentIn):
    model_config = ConfigDict(from_attributes=True)
    id: int


class PaymentIn(BaseModel):
    amount: int = Field(gt=0)
    date: Date | None = None  # по умолчанию — сегодня


class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    student_id: int
    amount: int
    date: Date


class Debtor(BaseModel):
    student_id: int
    name: str
    phone: str
    group: str
    monthly_amount: int
    paid: int
    debt: int


class DebtorsOut(BaseModel):
    month: str
    total_debt: int
    debtors: list[Debtor]
