import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


@pytest.fixture()
def client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    def override():
        with Session() as db:
            yield db

    app.dependency_overrides[get_db] = override
    yield TestClient(app)
    app.dependency_overrides.clear()


def student(c, name="Анна", amount=1000):
    r = c.post("/students", json={"name": name, "phone": "+998900000000", "group": "A1", "monthly_amount": amount})
    assert r.status_code == 201
    return r.json()["id"]


def pay(c, sid, amount, day):
    r = c.post(f"/students/{sid}/payments", json={"amount": amount, "date": day})
    assert r.status_code == 201


def debtors(c, month="2025-03"):
    r = c.get("/debtors", params={"month": month})
    assert r.status_code == 200
    return r.json()


def test_student_crud(client):
    sid = student(client)
    assert client.get("/students").json()[0]["name"] == "Анна"
    r = client.patch(f"/students/{sid}", json={"group": "B2", "monthly_amount": 2000})
    assert r.json()["group"] == "B2" and r.json()["monthly_amount"] == 2000
    assert client.delete(f"/students/{sid}").status_code == 204
    assert client.get(f"/students/{sid}").status_code == 404


def test_no_payments_is_full_debt(client):
    student(client)
    d = debtors(client)["debtors"]
    assert len(d) == 1 and d[0]["paid"] == 0 and d[0]["debt"] == 1000


def test_partial_payments_are_summed(client):
    sid = student(client)
    pay(client, sid, 300, "2025-03-05")
    pay(client, sid, 200, "2025-03-20")
    d = debtors(client)["debtors"][0]
    assert d["paid"] == 500 and d["debt"] == 500


def test_exact_and_overpayment_are_not_debtors(client):
    a, b = student(client, "Анна"), student(client, "Борис")
    pay(client, a, 1000, "2025-03-01")
    pay(client, b, 5000, "2025-03-01")
    assert debtors(client)["debtors"] == []


def test_month_boundaries(client):
    sid = student(client)
    pay(client, sid, 999, "2025-02-28")
    pay(client, sid, 500, "2025-03-31")
    pay(client, sid, 700, "2025-04-01")
    assert debtors(client, "2025-03")["debtors"][0]["paid"] == 500
    assert debtors(client, "2025-04")["debtors"][0]["paid"] == 700


def test_year_rollover(client):
    sid = student(client)
    pay(client, sid, 400, "2024-12-31")
    pay(client, sid, 600, "2025-01-01")
    assert debtors(client, "2024-12")["debtors"][0]["paid"] == 400
    assert debtors(client, "2025-01")["debtors"][0]["paid"] == 600


def test_total_and_order(client):
    a, b = student(client, "Анна", 1000), student(client, "Борис", 3000)
    pay(client, a, 400, "2025-03-10")
    data = debtors(client)
    assert [d["name"] for d in data["debtors"]] == ["Борис", "Анна"]
    assert data["total_debt"] == 3000 + 600


def test_payments_list_per_student(client):
    a, b = student(client, "Анна"), student(client, "Борис")
    pay(client, a, 100, "2025-03-01")
    pay(client, b, 200, "2025-03-02")
    r = client.get(f"/students/{a}/payments").json()
    assert len(r) == 1 and r[0]["amount"] == 100 and r[0]["date"] == "2025-03-01"


def test_validation_errors(client):
    sid = student(client)
    for bad in ["2025-13", "2025-3", "abc", "2025-00"]:
        assert client.get("/debtors", params={"month": bad}).status_code == 422
    assert client.post(f"/students/{sid}/payments", json={"amount": 0}).status_code == 422
    assert client.post("/students/999/payments", json={"amount": 10}).status_code == 404
    assert client.post("/students", json={"name": "X", "phone": "123", "group": "A", "monthly_amount": -5}).status_code == 422


def test_delete_cascades_payments(client):
    sid = student(client)
    pay(client, sid, 100, "2025-03-01")
    client.delete(f"/students/{sid}")
    assert client.get(f"/students/{sid}/payments").status_code == 404
    assert debtors(client)["debtors"] == []
