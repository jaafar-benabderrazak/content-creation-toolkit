export const runtime = "nodejs";
import { supabase } from "@/lib/supabase";

export async function GET(req: Request) {
  const url = new URL(req.url);
  const status = url.searchParams.get("status") || "";

  let query = supabase
    .from("videos")
    .select("id, title, tags, profile, status, notes, position")
    .order("position", { ascending: true });

  if (status && status !== "all") {
    query = query.eq("status", status);
  }

  const { data, error } = await query;

  if (error) {
    return Response.json({ error: error.message, entries: [] }, { status: 500 });
  }

  return Response.json({
    entries: data || [],
    total: data?.length || 0,
  });
}

export async function POST(req: Request) {
  const body = await req.json();
  const action = body.action || "";

  if (action === "add") {
    const maxPos = await supabase
      .from("videos")
      .select("position")
      .order("position", { ascending: false })
      .limit(1);
    const nextPos = ((maxPos.data?.[0]?.position as number) || 0) + 1;

    const { data, error } = await supabase
      .from("videos")
      .insert({
        title: body.title,
        tags: body.tags || "",
        profile: body.profile || "cinematic",
        notes: body.notes || "",
        status: "planned",
        position: nextPos,
      })
      .select("id, title")
      .single();

    if (error) return Response.json({ error: error.message }, { status: 500 });
    return Response.json({ id: data.id, title: data.title });
  }

  if (action === "update_status") {
    const { error } = await supabase
      .from("videos")
      .update({ status: body.status })
      .eq("id", body.id);
    return Response.json({ ok: !error });
  }

  if (action === "delete") {
    const { error } = await supabase
      .from("videos")
      .delete()
      .eq("id", body.id);
    return Response.json({ ok: !error });
  }

  return Response.json({ error: "action must be add/update_status/delete" }, { status: 400 });
}
