import { stageColor } from "@/lib/api";

interface Props { stage: string | null | undefined }

export function StageBadge({ stage }: Props) {
  const s = stage || "cold";
  return (
    <span className={`inline-block rounded px-2 py-0.5 text-xs font-medium capitalize ${stageColor(s)}`}>
      {s.replace("_", " ")}
    </span>
  );
}
