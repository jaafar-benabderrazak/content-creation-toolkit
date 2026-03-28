import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";

// NOTE: process.cwd() in Next.js resolves to the dashboard/ directory.
// Profiles live one level up at config/profiles/ in the git checkout.
// This works for local dev and Vercel preview deployments with the repo checked out.
// It will not work in production Vercel deployments where the filesystem is read-only.
const PROFILES_DIR = path.resolve(process.cwd(), "../config/profiles");

export async function GET() {
  try {
    const files = fs.readdirSync(PROFILES_DIR);
    const profiles = files
      .filter((f) => f.endsWith(".yaml"))
      .map((f) => f.replace(/\.yaml$/, ""))
      .sort();
    return NextResponse.json({ profiles });
  } catch {
    return NextResponse.json(
      { error: "profiles directory not found" },
      { status: 500 }
    );
  }
}
