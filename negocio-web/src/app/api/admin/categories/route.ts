import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import { prisma } from "@/lib/prisma";

function slugify(name: string) {
  return name
    .toLowerCase()
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "");
}

const categorySchema = z.object({
  name: z.string().min(1).max(60),
});

export async function GET() {
  const categories = await prisma.category.findMany({ orderBy: { sortOrder: "asc" } });
  return NextResponse.json({ categories });
}

export async function POST(req: NextRequest) {
  const json = await req.json();
  const parsed = categorySchema.safeParse(json);

  if (!parsed.success) {
    return NextResponse.json({ error: "Nombre inválido" }, { status: 400 });
  }

  const category = await prisma.category.create({
    data: { name: parsed.data.name, slug: slugify(parsed.data.name) },
  });

  return NextResponse.json({ category }, { status: 201 });
}
