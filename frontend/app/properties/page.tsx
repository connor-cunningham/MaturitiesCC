"use client";
import { useState } from "react";
import useSWR from "swr";
import Link from "next/link";
import { api, fmt } from "@/lib/api";
import { Property, PaginatedResponse } from "@/lib/types";
import { ScoreBadge } from "@/components/shared/ScoreBadge";
import { ExportButton } from "@/components/shared/ExportButton";

const fetcher = (url: string) => api.get(url).then(r => r.data);

export default function PropertiesPage() {
  const [filters, setFilters] = useState({ state: "", city: "", building_class: "", min_units: "", max_units: "" });
  const [page, setPage] = useState(1);

  const params = new URLSearchParams();
  Object.entries(filters).forEach(([k, v]) => { if (v) params.set(k, v); });
  params.set("page", String(page));
  params.set("limit", "50");

  const { data, isLoading } = useSWR<PaginatedResponse<Property>>(`/properties?${params}`, fetcher);
  const setFilter = (k: string, v: string) => { setFilters(f => ({ ...f, [k]: v })); setPage(1); };

  return (
    <div className="space-y-4 max-w-full">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-gray-900">Properties <span className="text-gray-400 font-normal text-base">({data?.total ?? "…"})</span></h1>
        <ExportButton href="/exports/properties" />
      </div>

      <div className="bg-white border border-gray-200 rounded-lg p-3 flex flex-wrap gap-3">
        {[
          ["State", "state", "TX"], ["City", "city", "Atlanta"],
          ["Class", "building_class", "A"], ["Min Units", "min_units", "100"],
        ].map(([label, key, ph]) => (
          <div key={key} className="flex items-center gap-1.5">
            <label className="text-xs text-gray-500">{label}</label>
            <input value={(filters as any)[key]} onChange={e => setFilter(key, e.target.value)}
              placeholder={ph} className="text-xs border border-gray-200 rounded px-2 py-1 w-24 outline-none focus:border-blue-400" />
          </div>
        ))}
        <button onClick={() => { setFilters({ state: "", city: "", building_class: "", min_units: "", max_units: "" }); setPage(1); }}
          className="text-xs text-gray-400 hover:text-gray-700 ml-auto">Clear</button>
      </div>

      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                {["Property", "City", "State", "Units", "Class", "Year Built", "Owner", "Score", ""].map((h, i) => (
                  <th key={i} className="text-left px-3 py-2.5 text-xs font-semibold text-gray-600">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {isLoading && <tr><td colSpan={9} className="text-center py-8 text-gray-400">Loading…</td></tr>}
              {data?.items.map(p => (
                <tr key={p.id} className="hover:bg-blue-50/30">
                  <td className="px-3 py-2 font-medium max-w-[200px]">
                    <Link href={`/properties/${p.id}`} className="text-blue-600 hover:underline truncate block">{p.display_name}</Link>
                    {p.submarket && <span className="text-xs text-gray-400">{p.submarket}</span>}
                  </td>
                  <td className="px-3 py-2 text-gray-700">{p.city || "—"}</td>
                  <td className="px-3 py-2 text-gray-700">{p.state || "—"}</td>
                  <td className="px-3 py-2 text-gray-700">{fmt.number(p.units)}</td>
                  <td className="px-3 py-2">
                    {p.building_class && (
                      <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${
                        p.building_class === "A" ? "bg-blue-100 text-blue-700" :
                        p.building_class === "B" ? "bg-green-100 text-green-700" :
                        "bg-orange-100 text-orange-700"}`}>
                        {p.building_class}
                      </span>
                    )}
                  </td>
                  <td className="px-3 py-2 text-gray-600">{p.year_built || "—"}</td>
                  <td className="px-3 py-2 max-w-[160px]">
                    {p.owner_id ? (
                      <Link href={`/owners/${p.owner_id}`} className="text-blue-600 hover:underline text-xs truncate block">
                        {p.owner_name}
                      </Link>
                    ) : "—"}
                  </td>
                  <td className="px-3 py-2"><ScoreBadge score={p.priority_score} size="sm" /></td>
                  <td className="px-3 py-2">
                    <Link href={`/properties/${p.id}`} className="text-xs text-blue-600 hover:underline">View</Link>
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
