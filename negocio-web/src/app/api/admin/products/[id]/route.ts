import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import { prisma } from "@/lib/prisma";

const updateSchema = z.object({
  name: z.string().min(1).max(120).optional(),
  description: z.string().max(500).optional(),
  priceCents: z.number().int().min(0).optional(),
  imageUrl: z.string().url().optional().or(z.literal("")),
  categoryId: z.string().min(1).optional(),
  available: z.boolean().optional(),
});

export async function PATCH(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const json = await req.json();
  const parsed = updateSchema.safeParse(json);

  if (!parsed.success) {
    return NextResponse.json({ error: "Datos inválidos" }, { status: 400 });
  }

  const { imageUrl, ...rest } = parsed.data;
  const product = await prisma.product.update({
    where: { id },
    data: { ...rest, ...(imageUrl !== undefined ? { imageUrl: imageUrl || null } : {}) },
  });

  return NextResponse.json({ product });
}

export async function DELETE(
  _req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  await prisma.product.delete({ where: { id } });
  return NextResponse.json({ ok: true });
}
