import { StackHandler } from "@stackframe/stack";
import { stackClientApp } from "@/stack/client";

export const dynamic = "force-dynamic";

export default function Handler(props: any) {
  return <StackHandler app={stackClientApp} {...props} />;
}
