import CheckoutForm from "./CheckoutForm";

export default function CheckoutPage() {
  return (
    <div className="container-page py-12">
      <h1 className="font-display text-3xl font-semibold text-ink-900">Finalizar pedido</h1>
      <p className="mt-2 text-ink-600">
        Tu pedido será para recoger en tienda. Elige el horario y método de pago.
      </p>
      <div className="mt-8">
        <CheckoutForm />
      </div>
    </div>
  );
}
