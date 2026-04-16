"use client";
import { useState } from "react";
import useSWR, { mutate } from "swr";
import Link from "next/link";
import { api, fmt } from "@/lib/api";
import { OutreachTarget, OUTREACH_STAGES, TARGET_TIERS } from "@/lib/types";
import { StageBadge } from "@/components/shared/StageBadge";
import { ExportButton } from "@/components/shared/ExportButton";
import { Plus } from "lucide-react";

const fetcher = (url: string) => api.get(url).then(r => r.data);

export default function PipelinePage() {
  const [stageFilter, setStageFilter] = useState("");
  const [tierFilter, setTierFilter] = useState("");

  const params = new URLSearchParams();
  if (stageFilter) params.set("stage", stageFilter);
  if (tierFilter) params.set("target_tier", tierFilter);

  const { data: targets, isLoading } = useSWR<OutreachTarget[]>(`/targets?${params}`, fetcher);

  const updateStage = async (id: string, stage: string) => {
    await api.patch(`/targets/${id}`, { stage });
    mutate(`/targets?${params}`);
  };

  const kanbanStages = ["identified", "researched", "outreach_sent", "contacted", "meeting_scheduled", "warm", "active"];
  const byStage: Record<string, OutreachTarget[]> = {};
  kanbanStages.forEach(s => { byStage[s] = []; });
  targets?.forEach(t => {
    if (byStage[t.stage]) byStage[t.stage].push(t);
    else byStage[t.stage] = [t];
  });

  return (
    <div className="space-y-4 max-w-full">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-gray-900">BD Pipeline</h1>
        <div className="flex gap-2">
          <ExportButton href="/exports/targets" label="Export Pipeline" />
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white border border-gray-200 rounded-lg p-3 flex gap-3">
        <select value={stageFilter} onChange={e => setStageFilter(e.target.value)}
          className="text-xs border border-gray-200 rounded px-2 py-1">
          <option value="">All Stages</option>
          {OUTREACH_STAGES.map(s => <option key={s} value={s}>{s.replace(/_/g, " ")}</option>)}
        </select>
        <select value={tierFilter} onChange={e => setTierFilter(e.target.value)}
          className="text-xs border border-gray-200 rounded px-2 py-1">
          <option value="">All Tiers</option>
          {TARGET_TIERS.map(t => <option key={t} value={t}>{t}</option>)}
        </select>
      </div>

      {/* Pipeline table */}
      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                {["Owner / Property", "Stage", "Tier", "Last Contact", "Next Follow-up", "Relationship", "Tags", ""].map((h, i) => (
                  <th key={i} className="text-left px-3 py-2.5 text-xs font-semibold text-gray-600">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {isLoading && <tr><td colSpan={8} className="text-center py-8 text-gray-400">Loading…</td></tr>}
              {targets?.map(t => (
                <tr key={t.id} className="hover:bg-blue-50/30">
                  <td className="px-3 py-2">
                    {t.owner_id && (
                      <Link href={`/owners/${t.owner_id}`} className="text-blue-600 hover:underline text-sm font-medium">
                        Owner
                      </Link>
                    )}
                    {t.property_id && (
                      <Link href={`/properties/${t.property_id}`} className="text-blue-600 hover:underline text-sm">
                        Property
                      </Link>
                    )}
                  </td>
                  <td className="px-3 py-2">
                    <select value={t.stage}
                      onChange={e => updateStage(t.id, e.target.value)}
                      className="text-xs border-0 outline-none bg-transparent cursor-pointer">
                      {OUTREACH_STAGES.map(s => (
                        <option key={s} value={s}>{s.replace(/_/g, " ")}</option>
                      ))}
                    </select>
                  </td>
                  <td className="px-3 py-2 text-xs text-gray-500">{t.target_tier || "—"}</td>
                  <td className="px-3 py-2 text-xs text-gray-600">{fmt.date(t.last_contact_date)}</td>
                  <td className="px-3 py-2 text-xs">
                    {t.next_followup_date ? (
                      <span className={`${new Date(t.next_followup_date) < new Date() ? "text-red-600 font-medium" : "text-gray-600"}`}>
                        {fmt.date(t.next_followup_date)}
                      </span>
                    ) : "—"}
                  </td>
                  <td className="px-3 py-2 text-xs text-gray-500 capitalize">{t.relationship_strength || "—"}</td>
                  <td className="px-3 py-2">
                    <div className="flex flex-wrap gap-1">
                      {t.tags?.map(tag => (
                        <span key={tag} className="text-xs bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded">{tag}</span>
                      ))}
                    </div>
                  </td>
                  <td className="px-3 py-2 text-xs text-gray-400 max-w-[200px] truncate">
                    {t.internal_notes}
                  </td>
                </tr>
              ))}
              {!isLoading && targets?.length === 0 && (
                <tr>
                  <td colSpan={8} className="text-center py-12 text-gray-400">
                    No pipeline targets yet. Add owners/properties to your pipeline from their detail pages.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
