import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { verifyCoinbaseWebhookSignature } from "@/lib/coinbase";

export async function POST(req: NextRequest) {
  const rawBody = await req.text();
  const signature = req.headers.get("x-cc-webhook-signature");

  if (!verifyCoinbaseWebhookSignature(rawBody, signature)) {
    return NextResponse.json({ error: "Firma inválida" }, { status: 401 });
  }

  const payload = JSON.parse(rawBody);
  const eventType = payload?.event?.type as string | undefined;
  const chargeId = payload?.event?.data?.id as string | undefined;

  if (!eventType || !chargeId) {
    return NextResponse.json({ error: "Evento inválido" }, { status: 400 });
  }

  const order = await prisma.order.findFirst({ where: { coinbaseChargeId: chargeId } });
  if (!order) {
    return NextResponse.json({ received: true });
  }

  if (eventType === "charge:confirmed") {
    if (order.status === "PENDING_PAYMENT") {
      await prisma.order.update({ where: { id: order.id }, data: { status: "PAID" } });
    }
  } else if (eventType === "charge:failed" || eventType === "charge:resolved") {
    if (order.status === "PENDING_PAYMENT" && eventType === "charge:failed") {
      await prisma.order.update({ where: { id: order.id }, data: { status: "CANCELLED" } });
    }
  }

  return NextResponse.json({ received: true });
}
