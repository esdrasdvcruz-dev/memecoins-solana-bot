import { prisma } from "@/lib/prisma";
import OrdersTable from "./OrdersTable";

export const dynamic = "force-dynamic";

export default async function AdminOrdersPage() {
  const orders = await prisma.order.findMany({
    include: { items: true },
    orderBy: { createdAt: "desc" },
    take: 100,
  });

  return (
    <div>
      <h1 className="font-display text-2xl font-semibold text-ink-900">Pedidos</h1>
      <p className="mt-1 text-sm text-ink-500">
        Los pedidos con transferencia internacional requieren confirmación manual tras verificar el
        comprobante.
      </p>
      <div className="mt-6">
        <OrdersTable
          orders={orders.map((o) => ({
            id: o.id,
            customerName: o.customerName,
            customerPhone: o.customerPhone,
            pickupTime: o.pickupTime.toISOString(),
            status: o.status,
            paymentMethod: o.paymentMethod,
            totalCents: o.totalCents,
            currency: o.currency,
            transferReference: o.transferReference,
            itemsSummary: o.items.map((i) => `${i.quantity}× ${i.nameSnapshot}`).join(", "),
          }))}
        />
      </div>
    </div>
  );
}
