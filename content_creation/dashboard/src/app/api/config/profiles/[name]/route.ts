import { NextRequest, NextResponse } from "next/server";
import fs from "fs";
import path from "path";
import * as yaml from "js-yaml";

const PROFILES_DIR = path.resolve(process.cwd(), "data/profiles");
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

    const ENV_VAR_MAP: Record<string, string> = {
      "notify.discord_webhook_url": "NOTF_DISCORD_WEBHOOK_URL",
      "notify.slack_webhook_url":   "NOTF_SLACK_WEBHOOK_URL",
      "suno.api_key":               "SUNO_API_KEY",
    };

    const provenance: Record<string, "env" | "yaml"> = {};
    for (const [fieldPath, envVar] of Object.entries(ENV_VAR_MAP)) {
      const [section, key] = fieldPath.split(".");
      const yamlValue = (data as Record<string, Record<string, unknown>>)[section]?.[key];
      const envValue = process.env[envVar];
      if ((yamlValue === null || yamlValue === undefined || yamlValue === "") && envValue) {
        provenance[fieldPath] = "env";
      } else {
        provenance[fieldPath] = "yaml";
      }
    }

    return NextResponse.json({ config: data, provenance });
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

  try {
    const body = await req.json();
    const yamlStr = yaml.dump(body, { lineWidth: 120 });
    // On Vercel, filesystem is read-only in production
    // Write will work in local dev but fail on Vercel — that's expected
    fs.writeFileSync(filePath, yamlStr, "utf-8");
    return NextResponse.json({ saved: true, profile: name });
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    if (message.includes("EROFS") || message.includes("read-only")) {
      return NextResponse.json(
        { error: "Filesystem is read-only on Vercel. Use local dev to save profiles." },
        { status: 403 }
      );
    }
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
