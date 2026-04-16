"use client";
import { useState } from "react";
import useSWR from "swr";
import Link from "next/link";
import { api, fmt } from "@/lib/api";
import { Loan, PaginatedResponse } from "@/lib/types";
import { ScoreBadge } from "@/components/shared/ScoreBadge";
import { MaturityBadge } from "@/components/shared/MaturityBadge";
import { ExportButton } from "@/components/shared/ExportButton";
import { ChevronUp, ChevronDown } from "lucide-react";

const fetcher = (url: string) => api.get(url).then(r => r.data);

export default function LoansPage() {
  const [filters, setFilters] = useState({
    maturity_start: "", maturity_end: "", state: "", lender: "",
    rate_type: "", min_amount: "", max_amount: "",
  });
  const [sort, setSort] = useState({ by: "maturity_date", dir: "asc" });
  const [page, setPage] = useState(1);

  const params = new URLSearchParams();
  Object.entries(filters).forEach(([k, v]) => { if (v) params.set(k, v); });
  params.set("sort_by", sort.by);
  params.set("sort_dir", sort.dir);
  params.set("page", String(page));
  params.set("limit", "50");

  const { data, isLoading } = useSWR<PaginatedResponse<Loan>>(`/loans?${params}`, fetcher);

  const setFilter = (k: string, v: string) => { setFilters(f => ({ ...f, [k]: v })); setPage(1); };
  const toggleSort = (col: string) => {
    setSort(s => ({ by: col, dir: s.by === col && s.dir === "asc" ? "desc" : "asc" }));
  };

  const SortIcon = ({ col }: { col: string }) => {
    if (sort.by !== col) return null;
    return sort.dir === "asc" ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />;
  };

  return (
    <div className="space-y-4 max-w-full">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-gray-900">Loans <span className="text-gray-400 text-base font-normal">({data?.total ?? "…"})</span></h1>
        <ExportButton href="/exports/loans" />
      </div>

      {/* Filters */}
      <div className="bg-white border border-gray-200 rounded-lg p-3 flex flex-wrap gap-3">
        <div className="flex items-center gap-1.5">
          <label className="text-xs text-gray-500">Maturity from</label>
          <input type="date" value={filters.maturity_start}
            onChange={e => setFilter("maturity_start", e.target.value)}
            className="text-xs border border-gray-200 rounded px-2 py-1 outline-none focus:border-blue-400" />
        </div>
        <div className="flex items-center gap-1.5">
          <label className="text-xs text-gray-500">to</label>
          <input type="date" value={filters.maturity_end}
            onChange={e => setFilter("maturity_end", e.target.value)}
            className="text-xs border border-gray-200 rounded px-2 py-1 outline-none focus:border-blue-400" />
        </div>
        <FilterInput label="State" value={filters.state} onChange={v => setFilter("state", v)} placeholder="TX" />
        <FilterInput label="Lender" value={filters.lender} onChange={v => setFilter("lender", v)} placeholder="Goldman…" />
        <select value={filters.rate_type} onChange={e => setFilter("rate_type", e.target.value)}
          className="text-xs border border-gray-200 rounded px-2 py-1 outline-none">
          <option value="">All Rate Types</option>
          <option value="floating">Floating</option>
          <option value="fixed">Fixed</option>
        </select>
        <FilterInput label="Min $" value={filters.min_amount} onChange={v => setFilter("min_amount", v)} placeholder="5000000" />
        <FilterInput label="Max $" value={filters.max_amount} onChange={v => setFilter("max_amount", v)} placeholder="100000000" />
        <button onClick={() => { setFilters({ maturity_start: "", maturity_end: "", state: "", lender: "", rate_type: "", min_amount: "", max_amount: "" }); setPage(1); }}
          className="text-xs text-gray-400 hover:text-gray-700 ml-auto">Clear</button>
      </div>

      {/* Table */}
      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200 sticky top-0">
              <tr>
                {[
                  ["maturity_date", "Maturity"],
                  ["", "Urgency"],
                  ["", "Property"],
                  ["", "Owner"],
                  ["", "Lender"],
                  ["original_amount", "Amount"],
                  ["", "Rate"],
                  ["", "IO"],
                  ["priority_score", "Score"],
                  ["", ""],
                ].map(([col, label], i) => (
                  <th key={i} className="text-left px-3 py-2.5 text-xs font-semibold text-gray-600 whitespace-nowrap">
                    {col ? (
                      <button onClick={() => toggleSort(col)} className="flex items-center gap-1 hover:text-gray-900">
                        {label} <SortIcon col={col} />
                      </button>
                    ) : label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {isLoading && (
                <tr><td colSpan={10} className="text-center py-8 text-gray-400">Loading…</td></tr>
              )}
              {data?.items.map(loan => (
                <tr key={loan.id} className="hover:bg-blue-50/30 transition-colors">
                  <td className="px-3 py-2 font-medium text-gray-900 whitespace-nowrap">{fmt.date(loan.maturity_date)}</td>
                  <td className="px-3 py-2"><MaturityBadge months={loan.months_to_maturity} /></td>
                  <td className="px-3 py-2 max-w-[200px]">
                    {loan.property_id ? (
                      <Link href={`/properties/${loan.property_id}`} className="text-blue-600 hover:underline truncate block">
                        {loan.property_name || "—"}
                      </Link>
                    ) : "—"}
                    {loan.property_city && <span className="text-xs text-gray-400">{loan.property_city}, {loan.property_state}</span>}
                  </td>
                  <td className="px-3 py-2 max-w-[160px]">
                    {loan.owner_id ? (
                      <Link href={`/owners/${loan.owner_id}`} className="text-blue-600 hover:underline truncate block text-xs">
                        {loan.owner_name || "—"}
                      </Link>
                    ) : "—"}
                  </td>
                  <td className="px-3 py-2 text-gray-700 truncate max-w-[140px]">{loan.lender || "—"}</td>
                  <td className="px-3 py-2 font-medium text-gray-900 whitespace-nowrap">{fmt.currency(loan.original_amount)}</td>
                  <td className="px-3 py-2">
                    <span className={`text-xs px-1.5 py-0.5 rounded ${loan.rate_type === "floating" ? "bg-orange-100 text-orange-700" : "bg-gray-100 text-gray-600"}`}>
                      {loan.rate_type || "—"}
                    </span>
                  </td>
                  <td className="px-3 py-2 text-center">
                    {loan.io_flag === true ? <span className="text-xs bg-purple-100 text-purple-700 px-1.5 py-0.5 rounded">IO</span>
                      : <span className="text-xs text-gray-400">Amort</span>}
                  </td>
                  <td className="px-3 py-2"><ScoreBadge score={loan.priority_score} size="sm" /></td>
                  <td className="px-3 py-2">
                    <Link href={`/loans/${loan.id}`} className="text-xs text-blue-600 hover:underline">View</Link>
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
              <button disabled={page <= 1} onClick={() => setPage(p => p - 1)}
                className="px-2 py-1 border rounded disabled:opacity-30">← Prev</button>
              <span>Page {page}</span>
              <button disabled={page * 50 >= data.total} onClick={() => setPage(p => p + 1)}
                className="px-2 py-1 border rounded disabled:opacity-30">Next →</button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function FilterInput({ label, value, onChange, placeholder }: {
  label: string; value: string; onChange: (v: string) => void; placeholder?: string
}) {
  return (
    <div className="flex items-center gap-1.5">
      <label className="text-xs text-gray-500">{label}</label>
      <input value={value} onChange={e => onChange(e.target.value)} placeholder={placeholder}
        className="text-xs border border-gray-200 rounded px-2 py-1 w-24 outline-none focus:border-blue-400" />
    </div>
  );
}
