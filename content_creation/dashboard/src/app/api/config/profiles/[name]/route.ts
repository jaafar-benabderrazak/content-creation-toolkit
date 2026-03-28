import { NextRequest, NextResponse } from "next/server";
import fs from "fs";
import path from "path";
import * as yaml from "js-yaml";

// NOTE: process.cwd() in Next.js resolves to the dashboard/ directory.
// Profiles live one level up at config/profiles/ in the git checkout.
// This works for local dev and Vercel preview deployments with the repo checked out.
// It will not work in production Vercel deployments where the filesystem is read-only.
const PROFILES_DIR = path.resolve(process.cwd(), "../config/profiles");
const NAME_PATTERN = /^[a-z0-9_-]+$/;

function profilePath(name: string): string {
  return path.resolve(PROFILES_DIR, name + ".yaml");
}

export async function GET(
  _req: NextRequest,
  { params }: { params: Promise<{ name: string }> }
) {
  const { name } = await params;

  if (!NAME_PATTERN.test(name)) {
    return NextResponse.json({ error: "Invalid profile name" }, { status: 400 });
  }

  const filePath = profilePath(name);
  if (!fs.existsSync(filePath)) {
    return NextResponse.json(
      { error: `Profile not found: ${name}` },
      { status: 404 }
    );
  }

  try {
    const raw = fs.readFileSync(filePath, "utf-8");
    const data = yaml.load(raw);
    return NextResponse.json(data);
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

export async function PUT(
  req: NextRequest,
  { params }: { params: Promise<{ name: string }> }
) {
  const { name } = await params;

  if (!NAME_PATTERN.test(name)) {
    return NextResponse.json({ error: "Invalid profile name" }, { status: 400 });
  }

  const filePath = profilePath(name);
  if (!fs.existsSync(filePath)) {
    return NextResponse.json(
      { error: `Profile not found: ${name}` },
      { status: 404 }
    );
  }

  try {
    const body = await req.json();
    const yamlStr = yaml.dump(body, { lineWidth: 120 });
    fs.writeFileSync(filePath, yamlStr, "utf-8");
    return NextResponse.json({ saved: true, profile: name });
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
