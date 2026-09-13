"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { formatCents } from "@/lib/money";
import StatusBadge from "@/components/StatusBadge";

type OrderRow = {
  id: string;
  customerName: string;
  customerPhone: string;
  pickupTime: string;
  status: string;
  paymentMethod: string;
  totalCents: number;
  currency: string;
  transferReference: string | null;
  itemsSummary: string;
};

const STATUS_OPTIONS = [
  "PENDING_PAYMENT",
  "PAID",
  "PREPARING",
  "READY_FOR_PICKUP",
  "COMPLETED",
  "CANCELLED",
];

const PAYMENT_LABELS: Record<string, string> = {
  CARD: "Tarjeta",
  BANK_TRANSFER_MX: "Transferencia MX",
  BANK_TRANSFER_INTL: "Transferencia internacional",
  CRYPTO: "Cripto",
};

export default function OrdersTable({ orders }: { orders: OrderRow[] }) {
  const router = useRouter();
  const [updating, setUpdating] = useState<string | null>(null);

  async function updateStatus(id: string, status: string) {
    setUpdating(id);
    await fetch(`/api/admin/orders/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status }),
    });
    setUpdating(null);
    router.refresh();
  }

  if (orders.length === 0) {
    return <p className="text-ink-500">Aún no hay pedidos.</p>;
  }

  return (
    <div className="overflow-x-auto rounded-2xl bg-white shadow-card">
      <table className="min-w-full divide-y divide-ink-100 text-sm">
        <thead className="bg-ink-50 text-left text-xs uppercase tracking-wide text-ink-500">
          <tr>
            <th className="px-4 py-3">Pedido</th>
            <th className="px-4 py-3">Cliente</th>
            <th className="px-4 py-3">Productos</th>
            <th className="px-4 py-3">Recolección</th>
            <th className="px-4 py-3">Pago</th>
            <th className="px-4 py-3">Total</th>
            <th className="px-4 py-3">Estado</th>
            <th className="px-4 py-3">Acciones</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-ink-100">
          {orders.map((o) => (
            <tr key={o.id} className={updating === o.id ? "opacity-50" : ""}>
              <td className="px-4 py-3 font-mono text-xs text-ink-500">
                #{o.id.slice(-8).toUpperCase()}
              </td>
              <td className="px-4 py-3">
                <div className="font-medium text-ink-900">{o.customerName}</div>
                <div className="text-xs text-ink-500">{o.customerPhone}</div>
              </td>
              <td className="max-w-xs px-4 py-3 text-ink-600">{o.itemsSummary}</td>
              <td className="px-4 py-3 text-ink-600">
                {new Intl.DateTimeFormat("es-MX", { dateStyle: "short", timeStyle: "short" }).format(
                  new Date(o.pickupTime)
                )}
              </td>
              <td className="px-4 py-3 text-ink-600">
                {PAYMENT_LABELS[o.paymentMethod] || o.paymentMethod}
                {o.paymentMethod === "BANK_TRANSFER_INTL" && o.transferReference && (
                  <div className="text-xs text-ink-400">{o.transferReference}</div>
                )}
              </td>
              <td className="px-4 py-3 font-medium text-ink-900">
                {formatCents(o.totalCents, o.currency)}
              </td>
              <td className="px-4 py-3">
                <StatusBadge status={o.status} />
              </td>
              <td className="px-4 py-3">
                <div className="flex flex-col gap-2">
                  <select
                    value={o.status}
                    disabled={updating === o.id}
                    onChange={(e) => updateStatus(o.id, e.target.value)}
                    className="rounded-lg border border-ink-200 px-2 py-1 text-xs"
                  >
                    {STATUS_OPTIONS.map((s) => (
                      <option key={s} value={s}>
                        {s}
                      </option>
                    ))}
                  </select>
                  {o.paymentMethod === "BANK_TRANSFER_INTL" && o.status === "PENDING_PAYMENT" && (
                    <button
                      onClick={() => updateStatus(o.id, "PAID")}
                      disabled={updating === o.id}
                      className="rounded-lg bg-green-600 px-2 py-1 text-xs font-medium text-white hover:bg-green-700"
                    >
                      Confirmar pago recibido
                    </button>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
