import { StackHandler } from "@stackframe/stack";
import { stackClientApp } from "@/stack/client";

export default function Handler(props: any) {
  return <StackHandler app={stackClientApp} {...props} />;
}
