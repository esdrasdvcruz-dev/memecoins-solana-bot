import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { verifyConektaWebhookSignature } from "@/lib/conekta";

export async function POST(req: NextRequest) {
  const rawBody = await req.text();
  const digest = req.headers.get("digest");

  if (!verifyConektaWebhookSignature(rawBody, digest)) {
    return NextResponse.json({ error: "Firma inválida" }, { status: 401 });
  }

  const event = JSON.parse(rawBody);
  const eventType = event?.type as string | undefined;
  const charge = event?.data?.object;
  const conektaOrderId = charge?.order_id as string | undefined;

  if (!eventType || !conektaOrderId) {
    return NextResponse.json({ error: "Evento inválido" }, { status: 400 });
  }

  const order = await prisma.order.findFirst({ where: { conektaOrderId } });
  if (!order) {
    // Puede ser un evento de una orden que no reconocemos; respondemos 200 para que Conekta no reintente.
    return NextResponse.json({ received: true });
  }

  if (eventType === "charge.paid") {
    if (order.status === "PENDING_PAYMENT") {
      await prisma.order.update({ where: { id: order.id }, data: { status: "PAID" } });
    }
  } else if (eventType === "charge.declined" || eventType === "charge.canceled") {
    if (order.status === "PENDING_PAYMENT") {
      await prisma.order.update({ where: { id: order.id }, data: { status: "CANCELLED" } });
    }
  }

  return NextResponse.json({ received: true });
}
