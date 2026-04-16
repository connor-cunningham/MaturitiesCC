"use client";
import useSWR from "swr";
import { api, fmt } from "@/lib/api";
import { DashboardSummary } from "@/lib/types";
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts";
import Link from "next/link";
import { ExportButton } from "@/components/shared/ExportButton";

const fetcher = (url: string) => api.get(url).then(r => r.data);

export default function DashboardPage() {
  const { data, isLoading } = useSWR<DashboardSummary>("/dashboard/summary", fetcher);

  if (isLoading) return <div className="text-gray-400 p-8">Loading…</div>;
  if (!data) return null;

  const { totals, maturity_counts, maturity_volumes, timeline, top_owners, top_states, top_lenders } = data;

  return (
    <div className="space-y-6 max-w-7xl">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-gray-900">Dashboard</h1>
        <div className="flex gap-2">
          <ExportButton href="/exports/loans" label="Export Loans" />
          <ExportButton href="/exports/owners" label="Export Owners" />
        </div>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Total Loans" value={fmt.number(totals.loans)} sub="tracked" />
        <StatCard label="Total Properties" value={fmt.number(totals.properties)} sub="tracked" />
        <StatCard label="Total Owners" value={fmt.number(totals.owners)} sub="tracked" />
        <StatCard label="Total Original Balance" value={fmt.currency(totals.original_balance)} sub="across all loans" />
      </div>

      {/* Maturity window cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <MaturityCard label="< 6 Months" count={maturity_counts.within_6mo} volume={maturity_volumes.within_6mo} urgency="high" />
        <MaturityCard label="< 12 Months" count={maturity_counts.within_12mo} volume={maturity_volumes.within_12mo} urgency="medium" />
        <MaturityCard label="< 24 Months" count={maturity_counts.within_24mo} volume={maturity_volumes.within_24mo} urgency="low" />
        <MaturityCard label="< 36 Months" count={maturity_counts.within_36mo} volume={maturity_volumes.within_36mo} urgency="none" />
      </div>

      {/* Maturity timeline chart */}
      <div className="bg-white rounded-lg border border-gray-200 p-5">
        <h2 className="font-semibold text-gray-800 mb-4">Maturity Timeline — Next 24 Months</h2>
        {timeline.length === 0 ? (
          <p className="text-gray-400 text-sm">No data</p>
        ) : (
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={timeline} margin={{ top: 5, right: 20, bottom: 5, left: 20 }}>
              <defs>
                <linearGradient id="vol" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#1d4ed8" stopOpacity={0.2} />
                  <stop offset="95%" stopColor="#1d4ed8" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="month" tick={{ fontSize: 11 }} />
              <YAxis tickFormatter={v => `$${(v / 1e6).toFixed(0)}M`} tick={{ fontSize: 11 }} width={55} />
              <Tooltip
                formatter={(v: any) => [fmt.currency(v), "Volume"]}
                labelFormatter={l => `Month: ${l}`}
              />
              <Area type="monotone" dataKey="volume" stroke="#1d4ed8" fill="url(#vol)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Top tables */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Top Owners */}
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-semibold text-gray-800 text-sm">Top Owners by Upcoming Volume</h2>
            <Link href="/owners" className="text-xs text-blue-600 hover:underline">View all</Link>
          </div>
          <div className="space-y-2">
            {top_owners.map((o, i) => (
              <Link key={o.id} href={`/owners/${o.id}`}
                className="flex items-center gap-2 py-1.5 hover:bg-gray-50 rounded px-1 group">
                <span className="text-xs text-gray-400 w-4">{i + 1}</span>
                <span className="flex-1 text-sm truncate text-gray-800 group-hover:text-blue-600">{o.name}</span>
                <span className="text-sm font-medium text-gray-700">{fmt.currency(o.total_volume)}</span>
                <span className="text-xs text-gray-400">{o.loan_count} loans</span>
              </Link>
            ))}
          </div>
        </div>

        {/* Top States */}
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <h2 className="font-semibold text-gray-800 text-sm mb-3">Top Markets by Volume</h2>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={top_states} layout="vertical" margin={{ left: 10, right: 20 }}>
              <XAxis type="number" tickFormatter={v => `$${(v / 1e6).toFixed(0)}M`} tick={{ fontSize: 10 }} />
              <YAxis type="category" dataKey="state" tick={{ fontSize: 11 }} width={28} />
              <Tooltip formatter={(v: any) => [fmt.currency(v), "Volume"]} />
              <Bar dataKey="total_volume" fill="#1d4ed8" radius={[0, 3, 3, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Top Lenders */}
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <h2 className="font-semibold text-gray-800 text-sm mb-3">Top Lenders</h2>
          <div className="space-y-2">
            {top_lenders.map((l, i) => (
              <div key={l.lender} className="flex items-center gap-2 py-1">
                <span className="text-xs text-gray-400 w-4">{i + 1}</span>
                <span className="flex-1 text-sm truncate text-gray-800">{l.lender}</span>
                <span className="text-sm font-medium text-gray-700">{fmt.currency(l.volume)}</span>
                <span className="text-xs text-gray-400">{l.count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({ label, value, sub }: { label: string; value: string; sub: string }) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <p className="text-xs text-gray-500 mb-1">{label}</p>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-xs text-gray-400">{sub}</p>
    </div>
  );
}

function MaturityCard({ label, count, volume, urgency }: {
  label: string; count: number; volume: number;
  urgency: "high" | "medium" | "low" | "none"
}) {
  const colors = {
    high: "border-red-300 bg-red-50",
    medium: "border-orange-200 bg-orange-50",
    low: "border-yellow-200 bg-yellow-50",
    none: "border-gray-200 bg-white",
  };
  return (
    <div className={`rounded-lg border p-4 ${colors[urgency]}`}>
      <p className="text-xs text-gray-600 mb-1">{label}</p>
      <p className="text-2xl font-bold text-gray-900">{count}</p>
      <p className="text-sm font-medium text-gray-600">{fmt.currency(volume)}</p>
    </div>
  );
}
