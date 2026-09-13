"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { formatCents } from "@/lib/money";

type Product = {
  id: string;
  name: string;
  description: string | null;
  priceCents: number;
  imageUrl: string | null;
  available: boolean;
  categoryId: string;
  categoryName: string;
};

type Category = { id: string; name: string };

export default function ProductsManager({
  initialProducts,
  categories,
}: {
  initialProducts: Product[];
  categories: Category[];
}) {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const [newName, setNewName] = useState("");
  const [newDescription, setNewDescription] = useState("");
  const [newPrice, setNewPrice] = useState("");
  const [newCategoryId, setNewCategoryId] = useState(categories[0]?.id || "");
  const [newImageUrl, setNewImageUrl] = useState("");

  const [newCategoryName, setNewCategoryName] = useState("");

  const [editingId, setEditingId] = useState<string | null>(null);
  const [editName, setEditName] = useState("");
  const [editPrice, setEditPrice] = useState("");

  async function handleCreateProduct(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    const priceCents = Math.round(parseFloat(newPrice) * 100);

    if (!newCategoryId || Number.isNaN(priceCents) || priceCents < 0) {
      setError("Revisa el precio y la categoría.");
      return;
    }

    setBusy(true);
    const res = await fetch("/api/admin/products", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: newName,
        description: newDescription || undefined,
        priceCents,
        categoryId: newCategoryId,
        imageUrl: newImageUrl || undefined,
      }),
    });
    setBusy(false);

    if (!res.ok) {
      const data = await res.json();
      setError(data.error || "No se pudo crear el producto.");
      return;
    }

    setNewName("");
    setNewDescription("");
    setNewPrice("");
    setNewImageUrl("");
    router.refresh();
  }

  async function handleCreateCategory(e: React.FormEvent) {
    e.preventDefault();
    if (!newCategoryName.trim()) return;
    setBusy(true);
    await fetch("/api/admin/categories", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: newCategoryName }),
    });
    setBusy(false);
    setNewCategoryName("");
    router.refresh();
  }

  async function toggleAvailable(product: Product) {
    setBusy(true);
    await fetch(`/api/admin/products/${product.id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ available: !product.available }),
    });
    setBusy(false);
    router.refresh();
  }

  function startEdit(product: Product) {
    setEditingId(product.id);
    setEditName(product.name);
    setEditPrice((product.priceCents / 100).toFixed(2));
  }

  async function saveEdit(productId: string) {
    const priceCents = Math.round(parseFloat(editPrice) * 100);
    setBusy(true);
    await fetch(`/api/admin/products/${productId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: editName, priceCents }),
    });
    setBusy(false);
    setEditingId(null);
    router.refresh();
  }

  async function deleteProduct(productId: string) {
    if (!confirm("¿Eliminar este producto? Esta acción no se puede deshacer.")) return;
    setBusy(true);
    await fetch(`/api/admin/products/${productId}`, { method: "DELETE" });
    setBusy(false);
    router.refresh();
  }

  return (
    <div className="space-y-8">
      <div className="grid gap-6 lg:grid-cols-[2fr_1fr]">
        <form onSubmit={handleCreateProduct} className="space-y-3 rounded-2xl bg-white p-6 shadow-card">
          <h2 className="font-display text-lg font-semibold text-ink-900">Nuevo producto</h2>
          <div className="grid gap-3 sm:grid-cols-2">
            <input
              required
              placeholder="Nombre"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              className="rounded-lg border border-ink-200 px-3 py-2"
            />
            <input
              required
              type="number"
              step="0.01"
              min="0"
              placeholder="Precio (MXN)"
              value={newPrice}
              onChange={(e) => setNewPrice(e.target.value)}
              className="rounded-lg border border-ink-200 px-3 py-2"
            />
            <select
              value={newCategoryId}
              onChange={(e) => setNewCategoryId(e.target.value)}
              className="rounded-lg border border-ink-200 px-3 py-2"
            >
              {categories.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
            <input
              placeholder="URL de imagen (opcional)"
              value={newImageUrl}
              onChange={(e) => setNewImageUrl(e.target.value)}
              className="rounded-lg border border-ink-200 px-3 py-2"
            />
          </div>
          <textarea
            placeholder="Descripción (opcional)"
            value={newDescription}
            onChange={(e) => setNewDescription(e.target.value)}
            rows={2}
            className="w-full rounded-lg border border-ink-200 px-3 py-2"
          />
          {error && <p className="text-sm text-red-600">{error}</p>}
          <button
            type="submit"
            disabled={busy}
            className="rounded-full bg-brand-500 px-5 py-2 text-sm font-semibold text-white hover:bg-brand-600 disabled:opacity-50"
          >
            Agregar producto
          </button>
        </form>

        <form onSubmit={handleCreateCategory} className="space-y-3 rounded-2xl bg-white p-6 shadow-card">
          <h2 className="font-display text-lg font-semibold text-ink-900">Nueva categoría</h2>
          <input
            placeholder="Nombre de categoría"
            value={newCategoryName}
            onChange={(e) => setNewCategoryName(e.target.value)}
            className="w-full rounded-lg border border-ink-200 px-3 py-2"
          />
          <button
            type="submit"
            disabled={busy}
            className="rounded-full bg-ink-900 px-5 py-2 text-sm font-semibold text-brand-50 hover:bg-ink-800 disabled:opacity-50"
          >
            Agregar categoría
          </button>
        </form>
      </div>

      <div className="overflow-x-auto rounded-2xl bg-white shadow-card">
        <table className="min-w-full divide-y divide-ink-100 text-sm">
          <thead className="bg-ink-50 text-left text-xs uppercase tracking-wide text-ink-500">
            <tr>
              <th className="px-4 py-3">Producto</th>
              <th className="px-4 py-3">Categoría</th>
              <th className="px-4 py-3">Precio</th>
              <th className="px-4 py-3">Disponible</th>
              <th className="px-4 py-3">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-ink-100">
            {initialProducts.map((p) => (
              <tr key={p.id}>
                <td className="px-4 py-3">
                  {editingId === p.id ? (
                    <input
                      value={editName}
                      onChange={(e) => setEditName(e.target.value)}
                      className="rounded-lg border border-ink-200 px-2 py-1"
                    />
                  ) : (
                    <span className="font-medium text-ink-900">{p.name}</span>
                  )}
                </td>
                <td className="px-4 py-3 text-ink-600">{p.categoryName}</td>
                <td className="px-4 py-3">
                  {editingId === p.id ? (
                    <input
                      type="number"
                      step="0.01"
                      value={editPrice}
                      onChange={(e) => setEditPrice(e.target.value)}
                      className="w-24 rounded-lg border border-ink-200 px-2 py-1"
                    />
                  ) : (
                    formatCents(p.priceCents)
                  )}
                </td>
                <td className="px-4 py-3">
                  <button
                    onClick={() => toggleAvailable(p)}
                    disabled={busy}
                    className={`rounded-full px-3 py-1 text-xs font-semibold ${
                      p.available ? "bg-green-100 text-green-800" : "bg-ink-100 text-ink-500"
                    }`}
                  >
                    {p.available ? "Disponible" : "Oculto"}
                  </button>
                </td>
                <td className="px-4 py-3">
                  <div className="flex gap-2">
                    {editingId === p.id ? (
                      <>
                        <button
                          onClick={() => saveEdit(p.id)}
                          disabled={busy}
                          className="rounded-lg bg-brand-500 px-3 py-1 text-xs font-semibold text-white hover:bg-brand-600"
                        >
                          Guardar
                        </button>
                        <button
                          onClick={() => setEditingId(null)}
                          className="rounded-lg border border-ink-200 px-3 py-1 text-xs"
                        >
                          Cancelar
                        </button>
                      </>
                    ) : (
                      <>
                        <button
                          onClick={() => startEdit(p)}
                          className="rounded-lg border border-ink-200 px-3 py-1 text-xs hover:bg-ink-100"
                        >
                          Editar
                        </button>
                        <button
                          onClick={() => deleteProduct(p.id)}
                          className="rounded-lg border border-red-200 px-3 py-1 text-xs text-red-600 hover:bg-red-50"
                        >
                          Eliminar
                        </button>
                      </>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
