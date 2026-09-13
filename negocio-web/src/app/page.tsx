import Link from "next/link";
import { prisma } from "@/lib/prisma";
import { businessConfig } from "@/lib/business-config";
import ProductCard from "@/components/ProductCard";

export default async function HomePage() {
  const featured = await prisma.product.findMany({
    where: { available: true },
    take: 3,
    orderBy: { createdAt: "asc" },
  });

  return (
    <div>
      <section className="border-b border-ink-100 bg-gradient-to-b from-brand-100/60 to-brand-50">
        <div className="container-page grid gap-10 py-16 sm:grid-cols-2 sm:items-center sm:py-24">
          <div>
            <h1 className="font-display text-4xl font-semibold leading-tight text-ink-900 sm:text-5xl">
              {businessConfig.name}
            </h1>
            <p className="mt-4 text-lg text-ink-600">{businessConfig.description}</p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link
                href="/menu"
                className="rounded-full bg-ink-900 px-6 py-3 text-sm font-semibold text-brand-50 transition hover:bg-ink-800"
              >
                Ver menú y ordenar
              </Link>
              <a
                href="#ubicacion"
                className="rounded-full border border-ink-200 px-6 py-3 text-sm font-semibold text-ink-800 transition hover:bg-ink-100"
              >
                Ubicación y horarios
              </a>
            </div>
            <div className="mt-8 flex flex-wrap gap-4 text-sm text-ink-600">
              <span className="rounded-full bg-white px-3 py-1 shadow-card">Recoge en tienda</span>
              <span className="rounded-full bg-white px-3 py-1 shadow-card">Tarjeta de crédito/débito</span>
              <span className="rounded-full bg-white px-3 py-1 shadow-card">Transferencia MX e internacional</span>
              <span className="rounded-full bg-white px-3 py-1 shadow-card">Criptomonedas</span>
            </div>
          </div>
          <div className="aspect-[4/3] w-full rounded-2xl bg-brand-200/60 shadow-card" />
        </div>
      </section>

      {featured.length > 0 && (
        <section className="container-page py-16">
          <div className="flex items-end justify-between">
            <h2 className="font-display text-2xl font-semibold text-ink-900">Destacados</h2>
            <Link href="/menu" className="text-sm font-medium text-brand-600 hover:underline">
              Ver menú completo →
            </Link>
          </div>
          <div className="mt-6 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {featured.map((product) => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
