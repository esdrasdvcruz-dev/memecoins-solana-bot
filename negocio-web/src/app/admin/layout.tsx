import Link from "next/link";
import LogoutButton from "./LogoutButton";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-ink-50">
      <div className="border-b border-ink-200 bg-white">
        <div className="container-page flex h-16 items-center justify-between">
          <nav className="flex items-center gap-6 text-sm font-medium text-ink-700">
            <span className="font-display text-lg font-semibold text-ink-900">Admin</span>
            <Link href="/admin" className="hover:text-brand-600">
              Pedidos
            </Link>
            <Link href="/admin/menu" className="hover:text-brand-600">
              Menú
            </Link>
          </nav>
          <LogoutButton />
        </div>
      </div>
      <div className="container-page py-10">{children}</div>
    </div>
  );
}
