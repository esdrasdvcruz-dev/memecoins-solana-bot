# Sitio web del negocio — pedidos en línea y recolección en tienda

Sitio construido con **Next.js 16 + TypeScript + Tailwind CSS + Prisma**. Permite a tus clientes
ver el menú, armar un carrito, pagar en línea y recoger su pedido en tienda. Incluye un panel de
administración para gestionar pedidos y el menú.

## Métodos de pago incluidos

| Método | Cómo funciona |
|---|---|
| Tarjeta de crédito/débito | [Conekta](https://conekta.com) — checkout hospedado (hosted checkout), redirección y confirmación automática por webhook. |
| Transferencia bancaria (México / SPEI) | También vía Conekta hosted checkout. |
| Transferencia internacional (SWIFT) | Flujo manual: se muestran tus datos bancarios y una referencia única; confirmas el pago manualmente desde el panel admin al recibir el comprobante. |
| Criptomonedas | [Coinbase Commerce](https://commerce.coinbase.com) — checkout hospedado, confirmación automática por webhook. |

Los precios y totales siempre se recalculan en el servidor a partir de la base de datos — nunca se
confía en lo que envía el navegador.

## Requisitos

- Node.js 20+ (ya instalado en esta máquina)
- Una base de datos (SQLite para desarrollo, incluida; Postgres recomendado para producción)

## Primeros pasos

```bash
npm install
cp .env.example .env   # ya existe un .env de desarrollo con SQLite
npx prisma migrate dev --name init
npm run db:seed        # crea categorías/productos de ejemplo y el usuario admin
npm run dev
```

Abre http://localhost:3000 para el sitio público y http://localhost:3000/admin/login para el panel
de administración (usa las credenciales que se muestran en la consola tras `npm run db:seed`,
definidas por `SEED_ADMIN_EMAIL` / `SEED_ADMIN_PASSWORD` en tu `.env`). **Cambia esa contraseña**
(por ahora, edítala directo en la base de datos o vuelve a correr el seed con nuevas credenciales)
antes de usar el sitio en producción.

## Personalizar tu negocio

- **Nombre, horarios, dirección, redes sociales:** edita `src/lib/business-config.ts`.
- **Colores de marca:** edita la paleta `brand` / `ink` en `tailwind.config.ts`.
- **Menú (productos y categorías):** desde el panel `/admin/menu`, o edita `prisma/seed.ts` para tu
  carga inicial.
- **Logo/imágenes de producto:** por ahora los productos usan un bloque de color como marcador; para
  usar imágenes reales, sube la URL en el campo "URL de imagen" al crear/editar un producto en el
  panel admin.

## Configurar los pagos reales

### Conekta (tarjeta + transferencia SPEI en México)

1. Crea una cuenta en https://panel.conekta.com
2. Ve a **Desarrollo → API Keys** y copia tu **llave privada**.
3. Configúrala en `.env` como `CONEKTA_PRIVATE_KEY`.
4. Ve a **Webhooks**, agrega la URL `https://tu-dominio.com/api/webhooks/conekta` y define un
   usuario/contraseña para autenticar las notificaciones. Ponlos en `.env` como
   `CONEKTA_WEBHOOK_USER` y `CONEKTA_WEBHOOK_PASSWORD`.
5. Empieza en modo de pruebas (test keys) y usa las [tarjetas de prueba de Conekta](https://developers.conekta.com/docs/tarjetas-de-prueba)
   antes de activar tu cuenta en modo producción (requiere verificación de tu negocio ante Conekta).

### Coinbase Commerce (criptomonedas)

1. Crea una cuenta en https://commerce.coinbase.com
2. Ve a **Settings → Security → API keys** y genera una API key. Ponla en `.env` como
   `COINBASE_COMMERCE_API_KEY`.
3. En la misma sección, configura un webhook con la URL
   `https://tu-dominio.com/api/webhooks/coinbase` y copia el **shared secret** a
   `COINBASE_COMMERCE_WEBHOOK_SECRET`.
4. Configura a qué wallet(s) quieres que se liquiden los pagos recibidos.

### Transferencia internacional (SWIFT)

No requiere ninguna cuenta adicional: solo completa tus datos bancarios reales en `.env`
(`INTL_BANK_NAME`, `INTL_BANK_ACCOUNT_HOLDER`, `INTL_BANK_IBAN_OR_ACCOUNT`, `INTL_BANK_SWIFT`).
Cuando un cliente elige este método, ve al panel `/admin` y pulsa **"Confirmar pago recibido"**
en su pedido una vez que verifiques el comprobante.

## Seguridad de la sesión de administrador

Genera un secreto propio y largo para `ADMIN_SESSION_SECRET` (por ejemplo con
`openssl rand -hex 32`) antes de desplegar a producción. Nunca reutilices el valor de ejemplo.

## Desplegar a producción

1. Usa una base de datos Postgres administrada (por ejemplo [Neon](https://neon.tech) o
   [Supabase](https://supabase.com)) y actualiza `DATABASE_URL`. Cambia también el `provider` en
   `prisma/schema.prisma` de `sqlite` a `postgresql`, y vuelve a correr
   `npx prisma migrate dev` localmente para regenerar las migraciones antes de desplegar.
2. Despliega en [Vercel](https://vercel.com) (soporte nativo de Next.js) u otro proveedor compatible
   con Node.js.
3. Define todas las variables de `.env.example` en el panel de variables de entorno de tu proveedor.
4. Actualiza `NEXT_PUBLIC_SITE_URL` a tu dominio real (se usa para las URLs de retorno de los pagos).
5. Registra las URLs de webhook reales (con tu dominio de producción) en Conekta y Coinbase Commerce.

## Estructura del proyecto

```
prisma/schema.prisma       Modelos: Category, Product, Order, OrderItem, AdminUser
src/lib/business-config.ts Datos del negocio (nombre, horarios, dirección, etc.)
src/lib/conekta.ts          Integración con Conekta (checkout + verificación de webhook)
src/lib/coinbase.ts         Integración con Coinbase Commerce (charge + verificación de webhook)
src/lib/cart-context.tsx    Carrito de compras (persistido en localStorage)
src/app/menu                Catálogo público
src/app/checkout            Formulario de pedido + selección de método de pago
src/app/pedido/[id]         Estado del pedido / instrucciones de pago
src/app/admin                Panel de administración (pedidos, menú)
src/app/api/checkout         Crea el pedido y arranca el pago
src/app/api/webhooks         Confirman pagos automáticamente (Conekta, Coinbase)
```
