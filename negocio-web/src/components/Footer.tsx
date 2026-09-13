import { businessConfig } from "@/lib/business-config";

export default function Footer() {
  return (
    <footer id="contacto" className="mt-20 border-t border-ink-100 bg-ink-900 text-brand-50">
      <div className="container-page grid gap-10 py-14 sm:grid-cols-3">
        <div>
          <h3 className="font-display text-lg font-semibold">{businessConfig.name}</h3>
          <p className="mt-2 text-sm text-brand-100/80">{businessConfig.tagline}</p>
        </div>
        <div id="ubicacion">
          <h4 className="text-sm font-semibold uppercase tracking-wide text-brand-200">
            Ubicación y horarios
          </h4>
          <p className="mt-2 text-sm text-brand-100/80">{businessConfig.address}</p>
          <ul className="mt-3 space-y-1 text-sm text-brand-100/80">
            {businessConfig.hours.map((h) => (
              <li key={h.day} className="flex justify-between gap-4">
                <span>{h.day}</span>
                <span>{h.time}</span>
              </li>
            ))}
          </ul>
        </div>
        <div>
          <h4 className="text-sm font-semibold uppercase tracking-wide text-brand-200">Contacto</h4>
          <ul className="mt-2 space-y-1 text-sm text-brand-100/80">
            <li>Tel/WhatsApp: {businessConfig.phone}</li>
            <li>Email: {businessConfig.email}</li>
          </ul>
        </div>
      </div>
      <div className="border-t border-ink-800 py-4 text-center text-xs text-brand-100/60">
        © {new Date().getFullYear()} {businessConfig.name}. Todos los derechos reservados.
      </div>
    </footer>
  );
}
