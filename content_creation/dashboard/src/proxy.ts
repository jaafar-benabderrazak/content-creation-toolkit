import { NextRequest, NextResponse } from "next/server";
import crypto from "crypto";

const SESSION_COOKIE = "dashboard_session";
const SESSION_SECRET = process.env.SESSION_SECRET || "fallback-dev-secret-change-in-production";

function verifyToken(token: string): boolean {
  try {
    const decoded = Buffer.from(token, "base64").toString("utf-8");
    const parts = decoded.split(":");
    if (parts.length < 3) return false;
    const hmac = parts.pop()!;
    const payload = parts.join(":");
    const expected = crypto.createHmac("sha256", SESSION_SECRET).update(payload).digest("hex");
    return hmac === expected;
  } catch {
    return false;
  }
}

export default function proxy(req: NextRequest) {
  const { pathname } = req.nextUrl;

  // Allow auth endpoints, login page, and static assets
  if (
    pathname === "/login" ||
    pathname === "/api/auth" ||
    pathname.startsWith("/_next") ||
    pathname === "/favicon.ico"
  ) {
    return NextResponse.next();
  }

  const token = req.cookies.get(SESSION_COOKIE)?.value;

  if (!token || !verifyToken(token)) {
    const loginUrl = new URL("/login", req.url);
    loginUrl.searchParams.set("from", pathname);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
