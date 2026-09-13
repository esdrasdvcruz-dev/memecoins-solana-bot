"use client";

import Link from "next/link";
import { useCart } from "@/lib/cart-context";

export default function CartButton() {
  const { totalCount } = useCart();

  return (
    <Link
      href="/carrito"
      className="relative inline-flex items-center gap-2 rounded-full bg-ink-900 px-4 py-2 text-sm font-medium text-brand-50 transition hover:bg-ink-800"
    >
      Carrito
      {totalCount > 0 && (
        <span className="inline-flex h-5 min-w-5 items-center justify-center rounded-full bg-brand-500 px-1 text-xs font-semibold text-white">
          {totalCount}
        </span>
      )}
    </Link>
  );
}
