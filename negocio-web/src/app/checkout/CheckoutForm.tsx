"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCart } from "@/lib/cart-context";
import { formatCents } from "@/lib/money";
import { businessConfig } from "@/lib/business-config";

type PaymentMethod = "CARD" | "BANK_TRANSFER_MX" | "BANK_TRANSFER_INTL" | "CRYPTO";

const PAYMENT_OPTIONS: { value: PaymentMethod; label: string; description: string }[] = [
  {
    value: "CARD",
    label: "Tarjeta de crédito o débito",
    description: "Pago seguro procesado por Conekta.",
  },
  {
    value: "BANK_TRANSFER_MX",
    label: "Transferencia bancaria (México / SPEI)",
    description: "Recibirás una referencia para transferir desde tu banco.",
  },
  {
    value: "BANK_TRANSFER_INTL",
    label: "Transferencia internacional (SWIFT)",
    description: "Te mostraremos los datos bancarios; la confirmación es manual.",
  },
  {
    value: "CRYPTO",
    label: "Criptomonedas",
    description: "Pago procesado por Coinbase Commerce (BTC, ETH, USDC y más).",
  },
];

function defaultPickupValue() {
  const d = new Date(Date.now() + (businessConfig.pickupLeadTimeMinutes + 5) * 60 * 1000);
  d.setSeconds(0, 0);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(
    d.getMinutes()
  )}`;
}

export default function CheckoutForm() {
  const { items, subtotalCents, clearCart } = useCart();
  const router = useRouter();

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [pickupTime, setPickupTime] = useState(defaultPickupValue());
  const [notes, setNotes] = useState("");
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>("CARD");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const minPickup = useMemo(defaultPickupValue, []);

  if (items.length === 0) {
    return (
      <div className="rounded-2xl bg-white p-8 text-center shadow-card">
        <p className="text-ink-600">Tu carrito está vacío.</p>
        <Link href="/menu" className="mt-4 inline-block text-brand-600 hover:underline">
          Ir al menú
        </Link>
      </div>
    );
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);

    try {
      const res = await fetch("/api/checkout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          items: items.map((i) => ({ productId: i.productId, quantity: i.quantity })),
          customer: { name, email, phone },
          pickupTime: new Date(pickupTime).toISOString(),
          notes: notes || undefined,
          paymentMethod,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        setError(data.error || "No se pudo procesar el pedido.");
        setSubmitting(false);
        return;
      }

      clearCart();

      if (data.redirectUrl.startsWith("http")) {
        window.location.href = data.redirectUrl;
      } else {
        router.push(data.redirectUrl);
      }
    } catch {
      setError("Ocurrió un error de conexión. Intenta de nuevo.");
      setSubmitting(false);
    }
  }

  return (
    <div className="grid gap-8 lg:grid-cols-[1fr_320px]">
      <form onSubmit={handleSubmit} className="space-y-6 rounded-2xl bg-white p-6 shadow-card">
        <div>
          <h2 className="font-display text-lg font-semibold text-ink-900">Tus datos</h2>
          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            <label className="text-sm font-medium text-ink-700">
              Nombre completo
              <input
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="mt-1 w-full rounded-lg border border-ink-200 px-3 py-2 text-ink-900 focus:border-brand-400 focus:outline-none"
              />
            </label>
            <label className="text-sm font-medium text-ink-700">
              Teléfono
              <input
                required
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                className="mt-1 w-full rounded-lg border border-ink-200 px-3 py-2 text-ink-900 focus:border-brand-400 focus:outline-none"
              />
            </label>
            <label className="text-sm font-medium text-ink-700 sm:col-span-2">
              Correo electrónico
              <input
                required
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="mt-1 w-full rounded-lg border border-ink-200 px-3 py-2 text-ink-900 focus:border-brand-400 focus:outline-none"
              />
            </label>
          </div>
        </div>

        <div>
          <h2 className="font-display text-lg font-semibold text-ink-900">Recolección en tienda</h2>
          <label className="mt-4 block text-sm font-medium text-ink-700">
            Fecha y hora para recoger tu pedido
            <input
              required
              type="datetime-local"
              min={minPickup}
              value={pickupTime}
              onChange={(e) => setPickupTime(e.target.value)}
              className="mt-1 w-full rounded-lg border border-ink-200 px-3 py-2 text-ink-900 focus:border-brand-400 focus:outline-none"
            />
          </label>
          <label className="mt-4 block text-sm font-medium text-ink-700">
            Notas para tu pedido (opcional)
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={3}
              className="mt-1 w-full rounded-lg border border-ink-200 px-3 py-2 text-ink-900 focus:border-brand-400 focus:outline-none"
            />
          </label>
        </div>

        <div>
          <h2 className="font-display text-lg font-semibold text-ink-900">Método de pago</h2>
          <div className="mt-4 space-y-3">
            {PAYMENT_OPTIONS.map((opt) => (
              <label
                key={opt.value}
                className={`flex cursor-pointer items-start gap-3 rounded-xl border p-4 transition ${
                  paymentMethod === opt.value
                    ? "border-brand-400 bg-brand-50"
                    : "border-ink-200 hover:border-ink-300"
                }`}
              >
                <input
                  type="radio"
                  name="paymentMethod"
                  className="mt-1"
                  checked={paymentMethod === opt.value}
                  onChange={() => setPaymentMethod(opt.value)}
                />
                <div>
                  <p className="font-medium text-ink-900">{opt.label}</p>
                  <p className="text-sm text-ink-500">{opt.description}</p>
                </div>
              </label>
            ))}
          </div>
        </div>

        {error && (
          <p className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">{error}</p>
        )}

        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded-full bg-brand-500 px-6 py-3 text-sm font-semibold text-white transition hover:bg-brand-600 disabled:opacity-50"
        >
          {submitting ? "Procesando..." : `Pagar ${formatCents(subtotalCents)}`}
        </button>
      </form>

      <aside className="h-fit rounded-2xl bg-white p-6 shadow-card">
        <h2 className="font-display text-lg font-semibold text-ink-900">Resumen</h2>
        <ul className="mt-4 space-y-2 text-sm">
          {items.map((item) => (
            <li key={item.productId} className="flex justify-between text-ink-700">
              <span>
                {item.quantity} × {item.name}
              </span>
              <span>{formatCents(item.priceCents * item.quantity)}</span>
            </li>
          ))}
        </ul>
        <div className="mt-4 flex justify-between border-t border-ink-100 pt-4 font-semibold text-ink-900">
          <span>Total</span>
          <span>{formatCents(subtotalCents)}</span>
        </div>
      </aside>
    </div>
  );
}
