import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import { prisma } from "@/lib/prisma";

const productSchema = z.object({
  name: z.string().min(1).max(120),
  description: z.string().max(500).optional(),
  priceCents: z.number().int().min(0),
  imageUrl: z.string().url().optional().or(z.literal("")),
  categoryId: z.string().min(1),
  available: z.boolean().optional(),
});

export async function GET() {
  const products = await prisma.product.findMany({
    include: { category: true },
    orderBy: { createdAt: "desc" },
  });
  return NextResponse.json({ products });
}

export async function POST(req: NextRequest) {
  const json = await req.json();
  const parsed = productSchema.safeParse(json);

  if (!parsed.success) {
    return NextResponse.json({ error: "Datos inválidos", details: parsed.error.flatten() }, { status: 400 });
  }

  const { imageUrl, ...rest } = parsed.data;
  const product = await prisma.product.create({
    data: { ...rest, imageUrl: imageUrl || null },
  });

  return NextResponse.json({ product }, { status: 201 });
}
