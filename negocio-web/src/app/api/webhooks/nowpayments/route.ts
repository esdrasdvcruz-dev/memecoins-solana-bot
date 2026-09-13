import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { verifyNowPaymentsSignature } from "@/lib/nowpayments";

const PAID_STATUSES = new Set(["confirmed", "sending", "finished"]);
const FAILED_STATUSES = new Set(["failed", "expired"]);

export async function POST(req: NextRequest) {
  const rawBody = await req.text();
  const signature = req.headers.get("x-nowpayments-sig");

  if (!verifyNowPaymentsSignature(rawBody, signature)) {
    return NextResponse.json({ error: "Firma inválida" }, { status: 401 });
  }

  const payload = JSON.parse(rawBody);
  const orderId = payload?.order_id as string | undefined;
  const paymentStatus = payload?.payment_status as string | undefined;

  if (!orderId || !paymentStatus) {
    return NextResponse.json({ error: "Evento inválido" }, { status: 400 });
  }

  const order = await prisma.order.findUnique({ where: { id: orderId } });
  if (!order) {
    return NextResponse.json({ received: true });
  }

  if (order.status === "PENDING_PAYMENT") {
    if (PAID_STATUSES.has(paymentStatus)) {
      await prisma.order.update({ where: { id: order.id }, data: { status: "PAID" } });
    } else if (FAILED_STATUSES.has(paymentStatus)) {
      await prisma.order.update({ where: { id: order.id }, data: { status: "CANCELLED" } });
    }
  }

  return NextResponse.json({ received: true });
}
