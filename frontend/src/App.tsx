import { useState } from "react";
import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AnimatePresence, motion } from "framer-motion";
import { ChevronLeft, ChevronRight, Plus, X } from "lucide-react";
import { addPayment, fmt, getDebtors, type Debtor } from "./api";

const MONTHS = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"];

const todayStr = () => new Date(Date.now() - new Date().getTimezoneOffset() * 60000).toISOString().slice(0, 10);
const currentMonth = () => todayStr().slice(0, 7);

function shiftMonth(month: string, delta: number) {
  const [y, m] = month.split("-").map(Number);
  const d = new Date(y, m - 1 + delta, 1);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
}

function plural(n: number, [one, few, many]: [string, string, string]) {
  const a = n % 10, b = n % 100;
  return a === 1 && b !== 11 ? one : a >= 2 && a <= 4 && (b < 10 || b >= 20) ? few : many;
}

function Ring({ value, size = 64 }: { value: number; size?: number }) {
  const r = size / 2 - 5;
  const c = 2 * Math.PI * r;
  const common = { cx: size / 2, cy: size / 2, r, fill: "none", strokeWidth: 5 };
  return (
    <div className="relative shrink-0" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90" aria-hidden>
        <circle {...common} stroke="var(--color-rule)" />
        <motion.circle
          {...common}
          stroke="var(--color-ink)"
          strokeLinecap="round"
          strokeDasharray={c}
          initial={{ strokeDashoffset: c }}
          animate={{ strokeDashoffset: c * (1 - value) }}
          transition={{ duration: 0.9, ease: "easeOut" }}
        />
      </svg>
      <span className="absolute inset-0 grid place-items-center text-xs font-semibold tabular-nums">
        {Math.floor(value * 100)}%
      </span>
    </div>
  );
}

function DebtorCard({ d, onPay }: { d: Debtor; onPay: () => void }) {
  return (
    <motion.li
      layout
      exit={{ opacity: 0, scale: 0.96 }}
      className="flex items-center gap-4 rounded-2xl border border-rule bg-sheet p-4"
    >
      <Ring value={Math.min(d.paid / d.monthly_amount, 1)} />
      <div className="min-w-0 flex-1">
        <p className="truncate font-display text-xl leading-tight">{d.name}</p>
        <p className="truncate text-sm text-muted">{d.group}</p>
        <a href={`tel:${d.phone}`} className="text-sm text-muted underline decoration-rule underline-offset-2">
          {d.phone}
        </a>
        <p className="mt-1 text-sm tabular-nums">
          Оплачено {fmt(d.paid)} из {fmt(d.monthly_amount)}
        </p>
      </div>
      <div className="flex flex-col items-end gap-2">
        <p className="font-display text-2xl font-semibold tabular-nums text-owed">{fmt(d.debt)}</p>
        <button
          onClick={onPay}
          className="inline-flex min-h-11 items-center gap-1 rounded-full bg-ink px-4 text-sm font-medium text-paper active:scale-95"
        >
          <Plus size={16} /> Оплата
        </button>
      </div>
    </motion.li>
  );
}

function PaySheet({ d, month, onClose }: { d: Debtor; month: string; onClose: () => void }) {
  const queryClient = useQueryClient();
  const [amount, setAmount] = useState(String(d.debt));
  const [date, setDate] = useState(month === currentMonth() ? todayStr() : `${month}-01`);
  const mutation = useMutation({
    mutationFn: () => addPayment(d.student_id, Number(amount), date),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["debtors"] });
      onClose();
    },
  });
  const valid = Number(amount) > 0 && Number.isInteger(Number(amount)) && date !== "";

  return (
    <>
      <motion.div
        className="fixed inset-0 z-20 bg-ink/40"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
      />
      <motion.div
        role="dialog"
        aria-label={`Оплата: ${d.name}`}
        className="fixed inset-x-0 bottom-0 z-30 mx-auto max-w-md rounded-t-3xl border border-b-0 border-rule bg-sheet p-5 pb-[max(1.25rem,env(safe-area-inset-bottom))]"
        initial={{ y: "100%" }}
        animate={{ y: 0 }}
        exit={{ y: "100%" }}
        transition={{ type: "spring", damping: 32, stiffness: 320 }}
      >
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="font-display text-2xl leading-tight">{d.name}</h2>
            <p className="text-sm text-muted">Долг {fmt(d.debt)}</p>
          </div>
          <button onClick={onClose} aria-label="Закрыть" className="grid size-11 place-items-center rounded-full">
            <X size={20} />
          </button>
        </div>

        <label className="mt-4 block text-sm text-muted" htmlFor="amount">Сумма</label>
        <input
          id="amount"
          autoFocus
          inputMode="numeric"
          pattern="[0-9]*"
          value={amount}
          onChange={(e) => setAmount(e.target.value.replace(/\D/g, ""))}
          className="w-full border-b-2 border-ink bg-transparent py-1 font-display text-5xl tabular-nums outline-none"
        />
        <button onClick={() => setAmount(String(d.debt))} className="mt-2 min-h-11 text-sm underline underline-offset-2">
          Весь долг
        </button>

        <label className="mt-2 block text-sm text-muted" htmlFor="date">Дата оплаты</label>
        <input
          id="date"
          type="date"
          value={date}
          onChange={(e) => setDate(e.target.value)}
          className="mt-1 min-h-11 w-full rounded-xl border border-rule bg-paper px-3"
        />

        {mutation.isError && <p className="mt-3 text-sm text-owed">{(mutation.error as Error).message}</p>}

        <button
          disabled={!valid || mutation.isPending}
          onClick={() => mutation.mutate()}
          className="mt-4 min-h-12 w-full rounded-full bg-ink font-medium text-paper disabled:opacity-40"
        >
          {mutation.isPending ? "Сохраняю…" : "Внести оплату"}
        </button>
      </motion.div>
    </>
  );
}

export default function App() {
  const [month, setMonth] = useState(currentMonth());
  const [paying, setPaying] = useState<Debtor | null>(null);
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["debtors", month],
    queryFn: () => getDebtors(month),
    placeholderData: keepPreviousData,
  });
  const [year, mon] = month.split("-").map(Number);
  const count = data?.debtors.length ?? 0;

  return (
    <main className="mx-auto max-w-md px-6 pb-16 pt-6">
      <div className="flex items-center justify-between">
        <button onClick={() => setMonth(shiftMonth(month, -1))} aria-label="Предыдущий месяц" className="grid size-11 place-items-center rounded-full border border-rule bg-sheet">
          <ChevronLeft size={20} />
        </button>
        <h1 className="font-display text-2xl">{MONTHS[mon - 1]} {year}</h1>
        <button onClick={() => setMonth(shiftMonth(month, 1))} aria-label="Следующий месяц" className="grid size-11 place-items-center rounded-full border border-rule bg-sheet">
          <ChevronRight size={20} />
        </button>
      </div>

      <section className="mt-8 border-y-2 border-double border-owed/60 py-5" aria-live="polite">
        <p className="text-sm text-muted">Осталось собрать</p>
        <p className="font-display text-6xl font-semibold leading-none tabular-nums text-owed">
          {data ? fmt(data.total_debt) : "…"}
        </p>
        <p className="mt-2 text-sm">
          {count} {plural(count, ["должник", "должника", "должников"])}
        </p>
      </section>

      {error && (
        <div className="mt-6">
          <p className="text-owed">Не удалось загрузить данные: {(error as Error).message}</p>
          <button onClick={() => refetch()} className="mt-2 min-h-11 underline">Повторить</button>
        </div>
      )}
      {isLoading && <p className="mt-6 text-muted">Загружаю…</p>}
      {data && count === 0 && (
        <p className="mt-6 font-display text-xl">В этом месяце долгов нет — все ученики оплатили занятия.</p>
      )}

      <ul className="mt-6 flex flex-col gap-3">
        <AnimatePresence initial={false}>
          {data?.debtors.map((d) => (
            <DebtorCard key={d.student_id} d={d} onPay={() => setPaying(d)} />
          ))}
        </AnimatePresence>
      </ul>

      <AnimatePresence>
        {paying && <PaySheet key={paying.student_id} d={paying} month={month} onClose={() => setPaying(null)} />}
      </AnimatePresence>
    </main>
  );
}
