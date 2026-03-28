import Link from "next/link";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";

export default function HomePage() {
  return (
    <div className="max-w-2xl">
      <h2 className="text-2xl font-bold tracking-tight mb-2">Overview</h2>
      <p className="text-muted-foreground mb-6">
        Manage your video generation pipeline from this control panel.
      </p>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Link href="/config">
          <Card className="hover:shadow-md transition-shadow cursor-pointer h-full">
            <CardHeader>
              <CardTitle className="text-base">Config Editor</CardTitle>
              <CardDescription>
                Edit pipeline YAML config, profiles, and prompt templates.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <span className="text-xs text-muted-foreground">/config</span>
            </CardContent>
          </Card>
        </Link>

        <Link href="/credits">
          <Card className="hover:shadow-md transition-shadow cursor-pointer h-full">
            <CardHeader>
              <CardTitle className="text-base">Credits</CardTitle>
              <CardDescription>
                Monitor Suno, Replicate, and OpenAI token usage and balances.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <span className="text-xs text-muted-foreground">/credits</span>
            </CardContent>
          </Card>
        </Link>

        <Link href="/status">
          <Card className="hover:shadow-md transition-shadow cursor-pointer h-full">
            <CardHeader>
              <CardTitle className="text-base">Status</CardTitle>
              <CardDescription>
                View live pipeline run status, logs, and trigger new runs.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <span className="text-xs text-muted-foreground">/status</span>
            </CardContent>
          </Card>
        </Link>
      </div>
    </div>
  );
}
