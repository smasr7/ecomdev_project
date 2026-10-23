export type Debtor = {
  student_id: number;
  name: string;
  phone: string;
  group: string;
  monthly_amount: number;
  paid: number;
  debt: number;
};
export type DebtorsResponse = { month: string; total_debt: number; debtors: Debtor[] };

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, { headers: { "Content-Type": "application/json" }, ...init });
  if (!res.ok) {
    let message = "Проверьте введённые данные";
    try {
      const body = await res.json();
      if (typeof body.detail === "string") message = body.detail;
    } catch {
      /* тело ответа не JSON */
    }
    throw new Error(message);
  }
  return res.json();
}

export const getDebtors = (month: string) => request<DebtorsResponse>(`/debtors?month=${month}`);

export const addPayment = (studentId: number, amount: number, date: string) =>
  request(`/students/${studentId}/payments`, { method: "POST", body: JSON.stringify({ amount, date }) });

export const fmt = (n: number) => new Intl.NumberFormat("ru-RU").format(n);
