import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import { randomBytes } from "crypto";
import { prisma } from "@/lib/prisma";
import { createHostedCheckoutOrder } from "@/lib/conekta";
import { createNowPaymentsInvoice } from "@/lib/nowpayments";

const checkoutSchema = z.object({
  items: z
    .array(
      z.object({
        productId: z.string().min(1),
        quantity: z.number().int().min(1).max(50),
      })
    )
    .min(1),
  customer: z.object({
    name: z.string().min(2).max(120),
    email: z.string().email(),
    phone: z.string().min(7).max(20),
  }),
  pickupTime: z.string().datetime({ offset: true }).or(z.string().min(1)),
  notes: z.string().max(500).optional(),
  paymentMethod: z.enum(["CARD", "BANK_TRANSFER_MX", "BANK_TRANSFER_INTL", "CRYPTO"]),
});

export async function POST(req: NextRequest) {
  const json = await req.json();
  const parsed = checkoutSchema.safeParse(json);

  if (!parsed.success) {
    return NextResponse.json(
      { error: "Datos inválidos", details: parsed.error.flatten() },
      { status: 400 }
    );
  }

  const { items, customer, pickupTime, notes, paymentMethod } = parsed.data;

  const productIds = items.map((i) => i.productId);
  const products = await prisma.product.findMany({ where: { id: { in: productIds } } });

  if (products.length !== productIds.length) {
    return NextResponse.json({ error: "Uno o más productos ya no existen." }, { status: 400 });
  }

  const unavailable = products.filter((p) => !p.available);
  if (unavailable.length > 0) {
    return NextResponse.json(
      { error: `Estos productos ya no están disponibles: ${unavailable.map((p) => p.name).join(", ")}` },
      { status: 400 }
    );
  }

  const pickupDate = new Date(pickupTime);
  if (Number.isNaN(pickupDate.getTime()) || pickupDate.getTime() < Date.now() + 10 * 60 * 1000) {
    return NextResponse.json(
      { error: "Selecciona un horario de recolección válido, al menos 10 minutos en el futuro." },
      { status: 400 }
    );
  }

  const productById = new Map(products.map((p) => [p.id, p]));
  let totalCents = 0;

  const orderItemsData = items.map((i) => {
    const product = productById.get(i.productId)!;
    totalCents += product.priceCents * i.quantity;
    return {
      productId: product.id,
      nameSnapshot: product.name,
      priceCentsSnapshot: product.priceCents,
      quantity: i.quantity,
    };
  });

  const order = await prisma.order.create({
    data: {
      customerName: customer.name,
      customerEmail: customer.email,
      customerPhone: customer.phone,
      pickupTime: pickupDate,
      notes,
      paymentMethod,
      subtotalCents: totalCents,
      totalCents,
      currency: "MXN",
      items: { create: orderItemsData },
    },
  });

  try {
    if (paymentMethod === "CARD" || paymentMethod === "BANK_TRANSFER_MX") {
      const { conektaOrderId, checkoutUrl } = await createHostedCheckoutOrder({
        orderId: order.id,
        currency: "MXN",
        customerName: customer.name,
        customerEmail: customer.email,
        customerPhone: customer.phone,
        items: orderItemsData.map((i) => ({
          name: i.nameSnapshot,
          unitPriceCents: i.priceCentsSnapshot,
          quantity: i.quantity,
        })),
        allowedPaymentMethods: paymentMethod === "CARD" ? ["card"] : ["bank_transfer"],
      });

      await prisma.order.update({ where: { id: order.id }, data: { conektaOrderId } });
      return NextResponse.json({ orderId: order.id, redirectUrl: checkoutUrl });
    }

    if (paymentMethod === "CRYPTO") {
      const { invoiceId, invoiceUrl } = await createNowPaymentsInvoice({
        orderId: order.id,
        description: `Pedido para recoger en tienda — ${customer.name}`,
        amountCents: totalCents,
      });

      await prisma.order.update({ where: { id: order.id }, data: { nowPaymentsInvoiceId: invoiceId } });
      return NextResponse.json({ orderId: order.id, redirectUrl: invoiceUrl });
    }

    // BANK_TRANSFER_INTL: flujo manual, sin pasarela automática.
    const transferReference = `INTL-${order.id.slice(-8).toUpperCase()}-${randomBytes(2)
      .toString("hex")
      .toUpperCase()}`;
    await prisma.order.update({ where: { id: order.id }, data: { transferReference } });
    return NextResponse.json({ orderId: order.id, redirectUrl: `/pedido/${order.id}` });
  } catch (err) {
    await prisma.order.update({ where: { id: order.id }, data: { status: "CANCELLED" } });
    const message = err instanceof Error ? err.message : "Error desconocido";
    return NextResponse.json(
      { error: `No se pudo iniciar el pago: ${message}` },
      { status: 502 }
    );
  }
}
