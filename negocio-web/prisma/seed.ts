import { PrismaClient } from "@prisma/client";
import bcrypt from "bcryptjs";

const prisma = new PrismaClient();

async function main() {
  const bebidas = await prisma.category.upsert({
    where: { slug: "bebidas" },
    update: {},
    create: { name: "Bebidas", slug: "bebidas", sortOrder: 1 },
  });

  const platillos = await prisma.category.upsert({
    where: { slug: "platillos" },
    update: {},
    create: { name: "Platillos", slug: "platillos", sortOrder: 0 },
  });

  const postres = await prisma.category.upsert({
    where: { slug: "postres" },
    update: {},
    create: { name: "Postres", slug: "postres", sortOrder: 2 },
  });

  const products = [
    {
      name: "Plato del día",
      description: "Nuestro platillo insignia, preparado al momento con ingredientes frescos.",
      priceCents: 15000,
      categoryId: platillos.id,
    },
    {
      name: "Entrada de la casa",
      description: "Una entrada ligera para abrir el apetito.",
      priceCents: 8000,
      categoryId: platillos.id,
    },
    {
      name: "Limonada natural",
      description: "Limonada fresca preparada al momento.",
      priceCents: 4500,
      categoryId: bebidas.id,
    },
    {
      name: "Café de la casa",
      description: "Café de grano seleccionado.",
      priceCents: 3800,
      categoryId: bebidas.id,
    },
    {
      name: "Postre del día",
      description: "Postre casero, receta de la casa.",
      priceCents: 6500,
      categoryId: postres.id,
    },
  ];

  for (const p of products) {
    const existing = await prisma.product.findFirst({ where: { name: p.name } });
    if (!existing) {
      await prisma.product.create({ data: p });
    }
  }

  const adminEmail = process.env.SEED_ADMIN_EMAIL || "admin@negocio.com";
  const adminPassword = process.env.SEED_ADMIN_PASSWORD || "CambiaEstaClave123";
  const passwordHash = await bcrypt.hash(adminPassword, 10);

  await prisma.adminUser.upsert({
    where: { email: adminEmail },
    update: { passwordHash },
    create: { email: adminEmail, passwordHash },
  });

  console.log("Seed completado.");
  console.log(`Admin: ${adminEmail} / ${adminPassword} (cambia esta clave después de tu primer login)`);
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
