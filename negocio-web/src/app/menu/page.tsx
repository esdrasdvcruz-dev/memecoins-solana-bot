import { prisma } from "@/lib/prisma";
import ProductCard from "@/components/ProductCard";

export const dynamic = "force-dynamic";

export default async function MenuPage() {
  const categories = await prisma.category.findMany({
    orderBy: { sortOrder: "asc" },
    include: {
      products: {
        where: { available: true },
        orderBy: { createdAt: "asc" },
      },
    },
  });

  return (
    <div className="container-page py-12">
      <h1 className="font-display text-3xl font-semibold text-ink-900">Nuestro menú</h1>
      <p className="mt-2 text-ink-600">
        Agrega tus platillos favoritos al carrito y elige tu horario de recolección en tienda.
      </p>

      {categories.length === 0 && (
        <p className="mt-10 text-ink-500">
          Aún no hay productos cargados. Ve al panel de administración para agregar tu menú.
        </p>
      )}

      <div className="mt-10 space-y-14">
        {categories.map(
          (category) =>
            category.products.length > 0 && (
              <section key={category.id}>
                <h2 className="font-display text-2xl font-semibold text-ink-900">{category.name}</h2>
                <div className="mt-6 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
                  {category.products.map((product) => (
                    <ProductCard key={product.id} product={product} />
                  ))}
                </div>
              </section>
            )
        )}
      </div>
    </div>
  );
}
