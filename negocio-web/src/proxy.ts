import { NextRequest, NextResponse } from "next/server";
import { jwtVerify } from "jose";
import { ADMIN_COOKIE_NAME } from "@/lib/auth";

export const config = {
  matcher: ["/admin/:path*", "/api/admin/:path*"],
};

export async function proxy(req: NextRequest) {
  const { pathname } = req.nextUrl;
  const isApi = pathname.startsWith("/api/admin");

  if (pathname === "/admin/login" || pathname === "/api/admin/login") {
    return NextResponse.next();
  }

  const token = req.cookies.get(ADMIN_COOKIE_NAME)?.value;
  const secret = process.env.ADMIN_SESSION_SECRET;

  const unauthorized = () =>
    isApi
      ? NextResponse.json({ error: "No autorizado" }, { status: 401 })
      : NextResponse.redirect(new URL("/admin/login", req.url));

  if (!token || !secret) {
    return unauthorized();
  }

  try {
    await jwtVerify(token, new TextEncoder().encode(secret));
    return NextResponse.next();
  } catch {
    return unauthorized();
  }
}
