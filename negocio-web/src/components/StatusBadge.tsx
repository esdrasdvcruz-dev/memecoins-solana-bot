const STATUS_LABELS: Record<string, string> = {
  PENDING_PAYMENT: "Pendiente de pago",
  PAID: "Pagado",
  PREPARING: "En preparación",
  READY_FOR_PICKUP: "Listo para recoger",
  COMPLETED: "Completado",
  CANCELLED: "Cancelado",
};

const STATUS_COLORS: Record<string, string> = {
  PENDING_PAYMENT: "bg-amber-100 text-amber-800",
  PAID: "bg-blue-100 text-blue-800",
  PREPARING: "bg-purple-100 text-purple-800",
  READY_FOR_PICKUP: "bg-green-100 text-green-800",
  COMPLETED: "bg-ink-100 text-ink-700",
  CANCELLED: "bg-red-100 text-red-700",
};

export default function StatusBadge({ status }: { status: string }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold ${
        STATUS_COLORS[status] || "bg-ink-100 text-ink-700"
      }`}
    >
      {STATUS_LABELS[status] || status}
    </span>
  );
}
