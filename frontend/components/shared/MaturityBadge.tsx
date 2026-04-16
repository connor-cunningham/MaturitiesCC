import { maturityUrgency, fmt } from "@/lib/api";

interface Props { months: number | null | undefined }

export function MaturityBadge({ months }: Props) {
  const cls = maturityUrgency(months);
  return (
    <span className={`inline-block rounded px-2 py-0.5 text-xs ${cls}`}>
      {fmt.months(months)}
    </span>
  );
}
