import { notFound } from "next/navigation";
import { prisma } from "@/lib/prisma";
import { formatCents } from "@/lib/money";
import StatusBadge from "@/components/StatusBadge";
import AutoRefresh from "@/components/AutoRefresh";

export const dynamic = "force-dynamic";

export default async function OrderStatusPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const order = await prisma.order.findUnique({
    where: { id },
    include: { items: true },
  });

  if (!order) notFound();

  return (
    <div className="container-page py-12">
      <div className="mx-auto max-w-2xl rounded-2xl bg-white p-8 shadow-card">
        <div className="flex items-center justify-between">
          <h1 className="font-display text-2xl font-semibold text-ink-900">
            Pedido #{order.id.slice(-8).toUpperCase()}
          </h1>
          <StatusBadge status={order.status} />
        </div>
        <p className="mt-2 text-sm text-ink-500">
          Recolección: {new Intl.DateTimeFormat("es-MX", { dateStyle: "full", timeStyle: "short" }).format(
            order.pickupTime
          )}
        </p>

        <ul className="mt-6 space-y-2 border-t border-ink-100 pt-4 text-sm">
          {order.items.map((item) => (
            <li key={item.id} className="flex justify-between text-ink-700">
              <span>
                {item.quantity} × {item.nameSnapshot}
              </span>
              <span>{formatCents(item.priceCentsSnapshot * item.quantity)}</span>
            </li>
          ))}
        </ul>
        <div className="mt-4 flex justify-between border-t border-ink-100 pt-4 font-semibold text-ink-900">
          <span>Total</span>
          <span>{formatCents(order.totalCents, order.currency)}</span>
        </div>

        {order.status === "PENDING_PAYMENT" && order.paymentMethod === "BANK_TRANSFER_INTL" && (
          <div className="mt-6 rounded-xl bg-brand-50 p-5 text-sm text-ink-800">
            <h2 className="font-semibold text-ink-900">Datos para transferencia internacional</h2>
            <dl className="mt-3 space-y-1">
              <div className="flex justify-between">
                <dt>Banco</dt>
                <dd>{process.env.INTL_BANK_NAME}</dd>
              </div>
              <div className="flex justify-between">
                <dt>Titular</dt>
                <dd>{process.env.INTL_BANK_ACCOUNT_HOLDER}</dd>
              </div>
              <div className="flex justify-between">
                <dt>Cuenta / IBAN</dt>
                <dd>{process.env.INTL_BANK_IBAN_OR_ACCOUNT}</dd>
              </div>
              <div className="flex justify-between">
                <dt>SWIFT</dt>
                <dd>{process.env.INTL_BANK_SWIFT}</dd>
              </div>
              <div className="flex justify-between font-semibold">
                <dt>Referencia (indícala en tu transferencia)</dt>
                <dd>{order.transferReference}</dd>
              </div>
            </dl>
            <p className="mt-4 text-ink-600">
              Una vez que realices la transferencia, envíanos tu comprobante por correo o WhatsApp
              indicando esta referencia. Confirmaremos tu pago manualmente y actualizaremos el estado
              de tu pedido.
            </p>
          </div>
        )}

        {order.status === "PENDING_PAYMENT" &&
          (order.paymentMethod === "CARD" ||
            order.paymentMethod === "BANK_TRANSFER_MX" ||
            order.paymentMethod === "CRYPTO") && (
            <div className="mt-6 rounded-xl bg-amber-50 p-5 text-sm text-amber-800">
              Estamos esperando la confirmación de tu pago. Esta página se actualizará automáticamente
              en cuanto se confirme.
              <AutoRefresh />
            </div>
          )}

        <p className="mt-6 text-center text-xs text-ink-400">
          Guarda esta página o el enlace para consultar el estado de tu pedido más tarde.
        </p>
      </div>
    </div>
  );
}
