"use client";

import Link from "next/link";
import { useCart } from "@/lib/cart-context";
import { formatCents } from "@/lib/money";

export default function CartPage() {
  const { items, updateQuantity, removeItem, subtotalCents } = useCart();

  if (items.length === 0) {
    return (
      <div className="container-page py-16 text-center">
        <h1 className="font-display text-3xl font-semibold text-ink-900">Tu carrito está vacío</h1>
        <p className="mt-3 text-ink-600">Explora el menú y agrega lo que se te antoje.</p>
        <Link
          href="/menu"
          className="mt-6 inline-block rounded-full bg-ink-900 px-6 py-3 text-sm font-semibold text-brand-50 hover:bg-ink-800"
        >
          Ver menú
        </Link>
      </div>
    );
  }

  return (
    <div className="container-page py-12">
      <h1 className="font-display text-3xl font-semibold text-ink-900">Tu carrito</h1>

      <div className="mt-8 divide-y divide-ink-100 rounded-2xl bg-white shadow-card">
        {items.map((item) => (
          <div key={item.productId} className="flex items-center gap-4 p-5">
            <div className="h-16 w-16 shrink-0 rounded-lg bg-brand-100" />
            <div className="flex-1">
              <p className="font-medium text-ink-900">{item.name}</p>
              <p className="text-sm text-ink-500">{formatCents(item.priceCents)} c/u</p>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => updateQuantity(item.productId, item.quantity - 1)}
                className="h-8 w-8 rounded-full border border-ink-200 text-ink-700 hover:bg-ink-100"
                aria-label="Disminuir cantidad"
              >
                −
              </button>
              <span className="w-6 text-center">{item.quantity}</span>
              <button
                onClick={() => updateQuantity(item.productId, item.quantity + 1)}
                className="h-8 w-8 rounded-full border border-ink-200 text-ink-700 hover:bg-ink-100"
                aria-label="Aumentar cantidad"
              >
                +
              </button>
            </div>
            <p className="w-24 text-right font-semibold text-ink-900">
              {formatCents(item.priceCents * item.quantity)}
            </p>
            <button
              onClick={() => removeItem(item.productId)}
              className="text-sm text-ink-400 hover:text-red-600"
              aria-label="Eliminar"
            >
              Eliminar
            </button>
          </div>
        ))}
      </div>

      <div className="mt-6 flex items-center justify-between rounded-2xl bg-white p-5 shadow-card">
        <span className="text-lg font-semibold text-ink-900">Subtotal</span>
        <span className="text-lg font-semibold text-ink-900">{formatCents(subtotalCents)}</span>
      </div>

      <div className="mt-6 flex justify-end">
        <Link
          href="/checkout"
          className="rounded-full bg-brand-500 px-8 py-3 text-sm font-semibold text-white hover:bg-brand-600"
        >
          Continuar al pago
        </Link>
      </div>
    </div>
  );
}
