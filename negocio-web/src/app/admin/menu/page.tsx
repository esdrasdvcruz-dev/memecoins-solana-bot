import { prisma } from "@/lib/prisma";
import ProductsManager from "./ProductsManager";

export const dynamic = "force-dynamic";

export default async function AdminMenuPage() {
  const [products, categories] = await Promise.all([
    prisma.product.findMany({ include: { category: true }, orderBy: { createdAt: "desc" } }),
    prisma.category.findMany({ orderBy: { sortOrder: "asc" } }),
  ]);

  return (
    <div>
      <h1 className="font-display text-2xl font-semibold text-ink-900">Menú</h1>
      <p className="mt-1 text-sm text-ink-500">
        Agrega, edita o desactiva productos. Los productos desactivados no aparecen en el menú público.
      </p>
      <div className="mt-6">
        <ProductsManager
          initialProducts={products.map((p) => ({
            id: p.id,
            name: p.name,
            description: p.description,
            priceCents: p.priceCents,
            imageUrl: p.imageUrl,
            available: p.available,
            categoryId: p.categoryId,
            categoryName: p.category.name,
          }))}
          categories={categories.map((c) => ({ id: c.id, name: c.name }))}
        />
      </div>
    </div>
  );
}
