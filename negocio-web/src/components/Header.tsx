import Link from "next/link";
import { businessConfig } from "@/lib/business-config";
import CartButton from "./CartButton";

export default function Header() {
  return (
    <header className="sticky top-0 z-40 border-b border-ink-100 bg-brand-50/95 backdrop-blur">
      <div className="container-page flex h-16 items-center justify-between">
        <Link href="/" className="font-display text-xl font-semibold text-ink-900">
          {businessConfig.name}
        </Link>
        <nav className="hidden items-center gap-8 text-sm font-medium text-ink-700 sm:flex">
          <Link href="/menu" className="hover:text-brand-600">
            Menú
          </Link>
          <Link href="/#ubicacion" className="hover:text-brand-600">
            Ubicación y horarios
          </Link>
          <Link href="/#contacto" className="hover:text-brand-600">
            Contacto
          </Link>
        </nav>
        <CartButton />
      </div>
    </header>
  );
}
