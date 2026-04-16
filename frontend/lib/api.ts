import axios from "axios";

const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export const api = axios.create({ baseURL: BASE });

// Helpers
export const fmt = {
  currency: (v: number | null | undefined) => {
    if (v == null) return "—";
    if (v >= 1_000_000) return `$${(v / 1_000_000).toFixed(1)}M`;
    if (v >= 1_000) return `$${(v / 1_000).toFixed(0)}K`;
    return `$${v.toFixed(0)}`;
  },
  pct: (v: number | null | undefined) => v == null ? "—" : `${(v * 100).toFixed(1)}%`,
  coupon: (v: number | null | undefined) => v == null ? "—" : `${v.toFixed(2)}%`,
  date: (v: string | null | undefined) => {
    if (!v) return "—";
    return new Date(v + "T00:00:00").toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
  },
  months: (v: number | null | undefined) => {
    if (v == null) return "—";
    if (v < 0) return "Matured";
    if (v < 12) return `${Math.round(v)}mo`;
    return `${(v / 12).toFixed(1)}yr`;
  },
  number: (v: number | null | undefined) => v == null ? "—" : v.toLocaleString(),
};

export const scoreColor = (score: number | null | undefined): string => {
  if (score == null) return "bg-gray-100 text-gray-500";
  if (score >= 75) return "bg-red-100 text-red-700";
  if (score >= 55) return "bg-orange-100 text-orange-700";
  if (score >= 35) return "bg-yellow-100 text-yellow-700";
  return "bg-green-100 text-green-700";
};

export const maturityUrgency = (months: number | null | undefined) => {
  if (months == null) return "bg-gray-100 text-gray-500";
  if (months < 6) return "bg-red-100 text-red-700 font-semibold";
  if (months < 12) return "bg-orange-100 text-orange-700";
  if (months < 24) return "bg-yellow-100 text-yellow-700";
  return "bg-gray-100 text-gray-600";
};

export const stageColor = (stage: string) => {
  const map: Record<string, string> = {
    warm: "bg-emerald-100 text-emerald-700",
    contacted: "bg-blue-100 text-blue-700",
    meeting_scheduled: "bg-purple-100 text-purple-700",
    outreach_sent: "bg-sky-100 text-sky-700",
    researched: "bg-indigo-100 text-indigo-700",
    cold: "bg-gray-100 text-gray-600",
    identified: "bg-slate-100 text-slate-600",
    active: "bg-teal-100 text-teal-700",
    closed: "bg-green-100 text-green-700",
    pass: "bg-red-100 text-red-600",
  };
  return map[stage] || "bg-gray-100 text-gray-600";
};
