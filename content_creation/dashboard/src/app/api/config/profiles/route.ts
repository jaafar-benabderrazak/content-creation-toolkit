import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";

// Profiles bundled in dashboard/data/profiles/ for Vercel deployment
const PROFILES_DIR = path.resolve(process.cwd(), "data/profiles");

export async function GET() {
  try {
    const files = fs.readdirSync(PROFILES_DIR);
    const profiles = files
      .filter((f: string) => f.endsWith(".yaml"))
      .map((f: string) => f.replace(/\.yaml$/, ""))
      .sort();
    return NextResponse.json({ profiles });
  } catch (err) {
    return NextResponse.json(
      { error: `profiles directory not found at ${PROFILES_DIR}`, detail: String(err) },
      { status: 500 }
    );
  }
}
