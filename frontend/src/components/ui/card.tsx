import { cn } from "@/lib/utils";
import type { HTMLAttributes } from "react";

export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "rounded-2xl border border-muted bg-surface p-6",
        className
      )}
      {...props}
    />
  );
}

export function KpiCard({
  label,
  value,
  sub,
  className,
}: {
  label: string;
  value: string;
  sub?: string;
  className?: string;
}) {
  return (
    <Card className={cn("hover:-translate-y-0.5 hover:shadow-lg", className)}>
      <p className="text-text-muted text-sm font-bold">{label}</p>
      <p className="font-heading text-2xl text-primary mt-1">{value}</p>
      {sub && <p className="text-xs text-text-muted mt-1">{sub}</p>}
    </Card>
  );
}