import crypto from "crypto";

const COINBASE_API_URL = "https://api.commerce.coinbase.com";

type CreateChargeParams = {
  orderId: string;
  name: string;
  description: string;
  amountCents: number;
  currency: string;
};

export async function createCoinbaseCharge(params: CreateChargeParams) {
  const apiKey = process.env.COINBASE_COMMERCE_API_KEY;
  if (!apiKey) {
    throw new Error("COINBASE_COMMERCE_API_KEY no está configurado en el entorno.");
  }

  const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000";

  const body = {
    name: params.name,
    description: params.description,
    pricing_type: "fixed_price",
    local_price: {
      amount: (params.amountCents / 100).toFixed(2),
      currency: params.currency,
    },
    metadata: {
      internal_order_id: params.orderId,
    },
    redirect_url: `${siteUrl}/pedido/${params.orderId}`,
    cancel_url: `${siteUrl}/pedido/${params.orderId}`,
  };

  const res = await fetch(`${COINBASE_API_URL}/charges`, {
    method: "POST",
    headers: {
      "X-CC-Api-Key": apiKey,
      "X-CC-Version": "2018-03-22",
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const errText = await res.text();
    throw new Error(`Error creando charge en Coinbase Commerce (${res.status}): ${errText}`);
  }

  const json = await res.json();
  return {
    chargeId: json.data.id as string,
    hostedUrl: json.data.hosted_url as string,
  };
}

export function verifyCoinbaseWebhookSignature(rawBody: string, signature: string | null): boolean {
  const secret = process.env.COINBASE_COMMERCE_WEBHOOK_SECRET;
  if (!secret || !signature) return false;

  const computed = crypto.createHmac("sha256", secret).update(rawBody).digest("hex");
  try {
    return crypto.timingSafeEqual(Buffer.from(computed), Buffer.from(signature));
  } catch {
    return false;
  }
}
