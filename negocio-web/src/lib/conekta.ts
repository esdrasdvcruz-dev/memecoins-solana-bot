import crypto from "crypto";

const CONEKTA_API_URL = "https://api.conekta.io";

type LineItem = {
  name: string;
  unitPriceCents: number;
  quantity: number;
};

type CreateHostedCheckoutParams = {
  orderId: string;
  currency: string;
  customerName: string;
  customerEmail: string;
  customerPhone: string;
  items: LineItem[];
  allowedPaymentMethods: Array<"card" | "bank_transfer">;
};

function getAuthHeader(): string {
  const privateKey = process.env.CONEKTA_PRIVATE_KEY;
  if (!privateKey) {
    throw new Error("CONEKTA_PRIVATE_KEY no está configurado en el entorno.");
  }
  return "Basic " + Buffer.from(`${privateKey}:`).toString("base64");
}

export async function createHostedCheckoutOrder(params: CreateHostedCheckoutParams) {
  const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000";

  const body = {
    currency: params.currency,
    customer_info: {
      name: params.customerName,
      email: params.customerEmail,
      phone: params.customerPhone,
    },
    line_items: params.items.map((item) => ({
      name: item.name,
      unit_price: item.unitPriceCents,
      quantity: item.quantity,
    })),
    metadata: {
      internal_order_id: params.orderId,
    },
    checkout: {
      allowed_payment_methods: params.allowedPaymentMethods,
      type: "HostedPayment",
      success_url: `${siteUrl}/pedido/${params.orderId}`,
      failure_url: `${siteUrl}/pedido/${params.orderId}`,
      expires_at: Math.floor(Date.now() / 1000) + 60 * 60 * 24,
    },
  };

  const res = await fetch(`${CONEKTA_API_URL}/orders`, {
    method: "POST",
    headers: {
      Accept: `application/vnd.conekta-v${process.env.CONEKTA_API_VERSION || "2.1.0"}+json`,
      "Content-Type": "application/json",
      Authorization: getAuthHeader(),
    },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const errText = await res.text();
    throw new Error(`Error creando orden en Conekta (${res.status}): ${errText}`);
  }

  const data = await res.json();
  return {
    conektaOrderId: data.id as string,
    checkoutUrl: data.checkout?.url as string,
  };
}

// El panel de Conekta entrega la llave pública "aplastada" en una sola línea, pero
// el decodificador PEM de Node/OpenSSL exige saltos de línea cada 64 caracteres en
// el cuerpo base64. Sin esto, crypto.createVerify falla con
// "DECODER routines::unsupported" y la verificación siempre da falso.
function normalizePem(key: string): string {
  const match = key
    .replace(/\r/g, "")
    .match(/-----BEGIN ([A-Z ]+)-----\s*([\s\S]*?)\s*-----END \1-----/);
  if (!match) return key;

  const [, label, body] = match;
  const compactBody = body.replace(/\s+/g, "");
  const wrappedBody = compactBody.match(/.{1,64}/g)?.join("\n") ?? compactBody;
  return `-----BEGIN ${label}-----\n${wrappedBody}\n-----END ${label}-----\n`;
}

// Conekta firma cada webhook con RSA-SHA256 sobre el cuerpo crudo (UTF-8) de la
// petición, enviando la firma en base64 en el header "Digest". Se verifica con la
// llave pública que genera el panel (Desarrollador -> Webhooks -> Llave de firma).
// https://developers.conekta.com/docs/autenticaci%C3%B3n-webhooks
export function verifyConektaWebhookSignature(rawBody: string, digestHeader: string | null): boolean {
  const rawPublicKey = process.env.CONEKTA_WEBHOOK_PUBLIC_KEY;
  if (!rawPublicKey || !digestHeader) return false;

  try {
    const publicKey = normalizePem(rawPublicKey);
    const verifier = crypto.createVerify("RSA-SHA256");
    verifier.update(rawBody, "utf8");
    verifier.end();
    return verifier.verify(publicKey, digestHeader, "base64");
  } catch {
    return false;
  }
}
