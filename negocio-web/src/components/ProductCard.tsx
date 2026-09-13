"use client";

import { useCart } from "@/lib/cart-context";
import { formatCents } from "@/lib/money";

type ProductCardProps = {
  product: {
    id: string;
    name: string;
    description: string | null;
    priceCents: number;
    imageUrl: string | null;
  };
};

export default function ProductCard({ product }: ProductCardProps) {
  const { addItem } = useCart();

  return (
    <div className="flex flex-col rounded-2xl bg-white p-5 shadow-card">
      <div className="mb-4 aspect-[4/3] w-full rounded-xl bg-brand-100" />
      <h3 className="font-display text-lg font-semibold text-ink-900">{product.name}</h3>
      {product.description && (
        <p className="mt-1 flex-1 text-sm text-ink-600">{product.description}</p>
      )}
      <div className="mt-4 flex items-center justify-between">
        <span className="font-semibold text-ink-900">{formatCents(product.priceCents)}</span>
        <button
          onClick={() =>
            addItem({
              productId: product.id,
              name: product.name,
              priceCents: product.priceCents,
              imageUrl: product.imageUrl,
            })
          }
          className="rounded-full bg-brand-500 px-4 py-2 text-sm font-semibold text-white transition hover:bg-brand-600"
        >
          Agregar
        </button>
      </div>
    </div>
  );
}
