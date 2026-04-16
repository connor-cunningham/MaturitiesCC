"use client";
import { useState } from "react";
import useSWR from "swr";
import Link from "next/link";
import { api, fmt } from "@/lib/api";
import { Owner, PaginatedResponse } from "@/lib/types";
import { ScoreBadge } from "@/components/shared/ScoreBadge";
import { StageBadge } from "@/components/shared/StageBadge";
import { ExportButton } from "@/components/shared/ExportButton";

const fetcher = (url: string) => api.get(url).then(r => r.data);

export default function OwnersPage() {
  const [filters, setFilters] = useState({ outreach_stage: "", target_tier: "", search: "" });
  const [sort, setSort] = useState({ by: "priority_score", dir: "desc" });
  const [page, setPage] = useState(1);

  const params = new URLSearchParams();
  Object.entries(filters).forEach(([k, v]) => { if (v) params.set(k, v); });
  params.set("sort_by", sort.by);
  params.set("sort_dir", sort.dir);
  params.set("page", String(page));
  params.set("limit", "50");

  const { data, isLoading } = useSWR<PaginatedResponse<Owner>>(`/owners?${params}`, fetcher);
  const setFilter = (k: string, v: string) => { setFilters(f => ({ ...f, [k]: v })); setPage(1); };

  return (
    <div className="space-y-4 max-w-full">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-gray-900">Owners <span className="text-gray-400 font-normal text-base">({data?.total ?? "…"})</span></h1>
        <ExportButton href="/exports/owners" />
      </div>

      <div className="bg-white border border-gray-200 rounded-lg p-3 flex flex-wrap gap-3">
        <div className="flex items-center gap-1.5">
          <label className="text-xs text-gray-500">Search</label>
          <input value={filters.search} onChange={e => setFilter("search", e.target.value)}
            placeholder="Owner name…"
            className="text-xs border border-gray-200 rounded px-2 py-1 w-36 outline-none focus:border-blue-400" />
        </div>
        <select value={filters.outreach_stage} onChange={e => setFilter("outreach_stage", e.target.value)}
          className="text-xs border border-gray-200 rounded px-2 py-1 outline-none">
          <option value="">All Stages</option>
          {["cold", "identified", "researched", "outreach_sent", "contacted", "meeting_scheduled", "warm", "active"].map(s => (
            <option key={s} value={s}>{s.replace(/_/g, " ")}</option>
          ))}
        </select>
        <select value={filters.target_tier} onChange={e => setFilter("target_tier", e.target.value)}
          className="text-xs border border-gray-200 rounded px-2 py-1 outline-none">
          <option value="">All Tiers</option>
          <option value="tier1">Tier 1</option>
          <option value="tier2">Tier 2</option>
          <option value="tier3">Tier 3</option>
        </select>
        <button onClick={() => { setFilters({ outreach_stage: "", target_tier: "", search: "" }); setPage(1); }}
          className="text-xs text-gray-400 hover:text-gray-700 ml-auto">Clear</button>
      </div>

      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                {["Owner", "HQ", "Stage", "Tier", "Properties", "Loans", "Upcoming 12mo", "Volume", "Score", ""].map((h, i) => (
                  <th key={i} className="text-left px-3 py-2.5 text-xs font-semibold text-gray-600 whitespace-nowrap">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {isLoading && <tr><td colSpan={10} className="text-center py-8 text-gray-400">Loading…</td></tr>}
              {data?.items.map(o => (
                <tr key={o.id} className="hover:bg-blue-50/30">
                  <td className="px-3 py-2 font-medium max-w-[200px]">
                    <Link href={`/owners/${o.id}`} className="text-blue-600 hover:underline truncate block">{o.display_name}</Link>
                  </td>
                  <td className="px-3 py-2 text-gray-600 text-xs">{o.hq_city}{o.hq_state && `, ${o.hq_state}`}</td>
                  <td className="px-3 py-2"><StageBadge stage={o.outreach_stage} /></td>
                  <td className="px-3 py-2 text-xs text-gray-500">{o.target_tier || "—"}</td>
                  <td className="px-3 py-2 text-gray-700 text-center">{o.property_count}</td>
                  <td className="px-3 py-2 text-gray-700 text-center">{o.loan_count}</td>
                  <td className="px-3 py-2 text-center">
                    {o.maturities_12mo > 0 ? (
                      <span className="text-xs font-semibold text-orange-700 bg-orange-100 px-1.5 py-0.5 rounded">
                        {o.maturities_12mo}
                      </span>
                    ) : <span className="text-gray-400">0</span>}
                  </td>
                  <td className="px-3 py-2 font-medium text-gray-900 whitespace-nowrap">{fmt.currency(o.total_upcoming_volume)}</td>
                  <td className="px-3 py-2"><ScoreBadge score={o.priority_score} size="sm" /></td>
                  <td className="px-3 py-2">
                    <Link href={`/owners/${o.id}`} className="text-xs text-blue-600 hover:underline">View</Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {data && (
          <div className="flex items-center justify-between px-4 py-2 border-t border-gray-100 text-xs text-gray-500">
            <span>{data.total} total</span>
            <div className="flex gap-2">
              <button disabled={page <= 1} onClick={() => setPage(p => p - 1)} className="px-2 py-1 border rounded disabled:opacity-30">← Prev</button>
              <span>Page {page}</span>
              <button disabled={page * 50 >= data.total} onClick={() => setPage(p => p + 1)} className="px-2 py-1 border rounded disabled:opacity-30">Next →</button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
