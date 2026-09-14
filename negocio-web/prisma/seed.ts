import { PrismaClient } from "@prisma/client";
import bcrypt from "bcryptjs";

const prisma = new PrismaClient();

async function main() {
  const shakes = await prisma.category.upsert({
    where: { slug: "shakes" },
    update: {},
    create: { name: "Shakes", slug: "shakes", sortOrder: 0 },
  });

  const bebidas = await prisma.category.upsert({
    where: { slug: "bebidas" },
    update: {},
    create: { name: "Bebidas", slug: "bebidas", sortOrder: 1 },
  });

  const snacks = await prisma.category.upsert({
    where: { slug: "snacks" },
    update: {},
    create: { name: "Snacks", slug: "snacks", sortOrder: 2 },
  });

  const products = [
    {
      name: "Shake de Fresa",
      description: "Fresa natural, leche y un toque de vainilla.",
      priceCents: 6500,
      categoryId: shakes.id,
    },
    {
      name: "Shake de Chocolate",
      description: "Cacao intenso con leche cremosa.",
      priceCents: 6500,
      categoryId: shakes.id,
    },
    {
      name: "Shake de Vainilla",
      description: "El clásico, cremoso y ligero.",
      priceCents: 6000,
      categoryId: shakes.id,
    },
    {
      name: "Shake Proteico de Plátano y Cacahuate",
      description: "Plátano, mantequilla de maní y proteína — ideal post-entreno.",
      priceCents: 8500,
      categoryId: shakes.id,
    },
    {
      name: "Shake Verde Detox",
      description: "Espinaca, manzana, apio y jengibre.",
      priceCents: 7500,
      categoryId: shakes.id,
    },
    {
      name: "Agua Embotellada",
      description: "500 ml.",
      priceCents: 2000,
      categoryId: bebidas.id,
    },
    {
      name: "Té Helado",
      description: "Preparado al momento, sin azúcar añadida.",
      priceCents: 3500,
      categoryId: bebidas.id,
    },
    {
      name: "Café Americano",
      description: "Grano de origen mexicano.",
      priceCents: 3000,
      categoryId: bebidas.id,
    },
    {
      name: "Barra de Granola",
      description: "Avena, miel y frutos secos.",
      priceCents: 2500,
      categoryId: snacks.id,
    },
    {
      name: "Mix de Nueces",
      description: "Almendra, nuez y arándano deshidratado.",
      priceCents: 3000,
      categoryId: snacks.id,
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
