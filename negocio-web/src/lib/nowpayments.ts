import crypto from "crypto";

const NOWPAYMENTS_API_URL = "https://api.nowpayments.io/v1";

type CreateInvoiceParams = {
  orderId: string;
  description: string;
  amountCents: number;
};

export async function createNowPaymentsInvoice(params: CreateInvoiceParams) {
  const apiKey = process.env.NOWPAYMENTS_API_KEY;
  if (!apiKey) {
    throw new Error("NOWPAYMENTS_API_KEY no está configurado en el entorno.");
  }

  const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000";
  // Verifica en tu cuenta de NOWPayments qué monedas fiat admite para conversión;
  // si "mxn" no está soportada, cambia esta variable a "usd" en tu .env.
  const priceCurrency = (process.env.NOWPAYMENTS_PRICE_CURRENCY || "mxn").toLowerCase();

  const body = {
    price_amount: params.amountCents / 100,
    price_currency: priceCurrency,
    order_id: params.orderId,
    order_description: params.description,
    ipn_callback_url: `${siteUrl}/api/webhooks/nowpayments`,
    success_url: `${siteUrl}/pedido/${params.orderId}`,
    cancel_url: `${siteUrl}/pedido/${params.orderId}`,
  };

  const res = await fetch(`${NOWPAYMENTS_API_URL}/invoice`, {
    method: "POST",
    headers: {
      "x-api-key": apiKey,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const errText = await res.text();
    throw new Error(`Error creando invoice en NOWPayments (${res.status}): ${errText}`);
  }

  const data = await res.json();
  return {
    invoiceId: String(data.id),
    invoiceUrl: data.invoice_url as string,
  };
}

// Sigue el esquema de verificación documentado por NOWPayments:
// ordenar las llaves del body alfabéticamente, convertir a string y firmar con HMAC-SHA512.
export function verifyNowPaymentsSignature(rawBody: string, signature: string | null): boolean {
  const secret = process.env.NOWPAYMENTS_IPN_SECRET;
  if (!secret || !signature) return false;

  let parsed: Record<string, unknown>;
  try {
    parsed = JSON.parse(rawBody);
  } catch {
    return false;
  }

  const sortedKeys = Object.keys(parsed).sort();
  const computed = crypto
    .createHmac("sha512", secret)
    .update(JSON.stringify(parsed, sortedKeys))
    .digest("hex");

  try {
    return crypto.timingSafeEqual(Buffer.from(computed), Buffer.from(signature));
  } catch {
    return false;
  }
}
