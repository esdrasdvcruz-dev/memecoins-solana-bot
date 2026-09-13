import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { verifyConektaWebhookAuth } from "@/lib/conekta";

export async function POST(req: NextRequest) {
  const authHeader = req.headers.get("authorization");
  if (!verifyConektaWebhookAuth(authHeader)) {
    return NextResponse.json({ error: "No autorizado" }, { status: 401 });
  }

  const event = await req.json();
  const eventType = event?.type as string | undefined;
  const conektaOrderId = event?.data?.object?.id as string | undefined;

  if (!eventType || !conektaOrderId) {
    return NextResponse.json({ error: "Evento inválido" }, { status: 400 });
  }

  const order = await prisma.order.findFirst({ where: { conektaOrderId } });
  if (!order) {
    // Puede ser un evento de una orden que no reconocemos; respondemos 200 para que Conekta no reintente.
    return NextResponse.json({ received: true });
  }

  if (eventType === "order.paid") {
    if (order.status === "PENDING_PAYMENT") {
      await prisma.order.update({ where: { id: order.id }, data: { status: "PAID" } });
    }
  } else if (eventType === "order.expired" || eventType === "order.canceled") {
    if (order.status === "PENDING_PAYMENT") {
      await prisma.order.update({ where: { id: order.id }, data: { status: "CANCELLED" } });
    }
  }

  return NextResponse.json({ received: true });
}
