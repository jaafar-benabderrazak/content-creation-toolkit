export const runtime = "nodejs";
import { supabase } from "@/lib/supabase";

export async function GET() {
  const { data, error } = await supabase
    .from("executions")
    .select("*")
    .order("started_at", { ascending: false })
    .limit(30);

  if (error) {
    return Response.json({ error: error.message, entries: [] }, { status: 500 });
  }

  return Response.json({ entries: data || [] });
}
