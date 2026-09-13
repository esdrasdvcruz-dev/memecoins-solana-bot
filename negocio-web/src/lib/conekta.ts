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

export function verifyConektaWebhookAuth(authorizationHeader: string | null): boolean {
  const expectedUser = process.env.CONEKTA_WEBHOOK_USER;
  const expectedPassword = process.env.CONEKTA_WEBHOOK_PASSWORD;
  if (!expectedUser || !expectedPassword) return false;
  if (!authorizationHeader?.startsWith("Basic ")) return false;

  const decoded = Buffer.from(authorizationHeader.slice(6), "base64").toString("utf-8");
  const [user, password] = decoded.split(":");
  return user === expectedUser && password === expectedPassword;
}
