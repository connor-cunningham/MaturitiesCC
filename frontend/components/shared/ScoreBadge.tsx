import { scoreColor } from "@/lib/api";

interface Props { score: number | null | undefined; size?: "sm" | "md" }

export function ScoreBadge({ score, size = "md" }: Props) {
  const cls = scoreColor(score);
  const text = score != null ? score.toFixed(0) : "—";
  const sz = size === "sm" ? "text-xs px-1.5 py-0.5" : "text-sm px-2 py-0.5";
  return (
    <span className={`inline-block rounded font-semibold ${cls} ${sz}`}>
      {text}
    </span>
  );
}
