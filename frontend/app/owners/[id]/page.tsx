"use client";
import { use, useState } from "react";
import useSWR, { mutate } from "swr";
import Link from "next/link";
import { api, fmt } from "@/lib/api";
import { Owner, OUTREACH_STAGES } from "@/lib/types";
import { ScoreBadge } from "@/components/shared/ScoreBadge";
import { StageBadge } from "@/components/shared/StageBadge";
import { MaturityBadge } from "@/components/shared/MaturityBadge";
import { NoteEditor } from "@/components/shared/NoteEditor";
import { ExportButton } from "@/components/shared/ExportButton";
import { ArrowLeft, Building2, FileText } from "lucide-react";

const fetcher = (url: string) => api.get(url).then(r => r.data);

export default function OwnerDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { data: owner, isLoading } = useSWR<Owner>(`/owners/${id}`, fetcher);
  const { data: portfolio } = useSWR(`/owners/${id}/portfolio`, fetcher);
  const [editStage, setEditStage] = useState(false);
  const [stage, setStage] = useState("");

  if (isLoading) return <div className="text-gray-400 p-8">Loading…</div>;
  if (!owner) return <div className="p-8 text-red-500">Owner not found</div>;

  const updateStage = async (s: string) => {
    await api.patch(`/owners/${id}`, { outreach_stage: s });
    mutate(`/owners/${id}`);
    setEditStage(false);
  };

  return (
    <div className="max-w-6xl space-y-5">
      <div className="flex items-center gap-3">
        <Link href="/owners" className="text-gray-400 hover:text-gray-700"><ArrowLeft className="w-5 h-5" /></Link>
        <h1 className="text-xl font-bold text-gray-900 flex-1">{owner.display_name}</h1>
        {editStage ? (
          <select autoFocus value={stage || owner.outreach_stage} onChange={e => updateStage(e.target.value)}
            onBlur={() => setEditStage(false)}
            className="text-xs border border-gray-300 rounded px-2 py-1">
            {OUTREACH_STAGES.map(s => <option key={s} value={s}>{s.replace(/_/g, " ")}</option>)}
          </select>
        ) : (
          <button onClick={() => { setStage(owner.outreach_stage); setEditStage(true); }}>
            <StageBadge stage={owner.outreach_stage} />
          </button>
        )}
        <ScoreBadge score={owner.priority_score} />
        <ExportButton href="/exports/owners" label="Export" />
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <InfoCard label="Properties" value={String(owner.property_count)} />
        <InfoCard label="Total Units" value={fmt.number(owner.total_units)} />
        <InfoCard label="Maturities (12mo)" value={String(owner.maturities_12mo)} highlight={owner.maturities_12mo > 0} />
        <InfoCard label="Upcoming Volume" value={fmt.currency(owner.total_upcoming_volume)} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {/* Owner details */}
        <div className="bg-white rounded-lg border border-gray-200 p-5 space-y-3">
          <h2 className="font-semibold text-gray-800">Owner Profile</h2>
          <dl className="space-y-2">
            <Field label="HQ" value={owner.hq_city && owner.hq_state ? `${owner.hq_city}, ${owner.hq_state}` : (owner.hq_city || owner.hq_state)} />
            <Field label="Type" value={owner.ownership_type} />
            <Field label="Website" value={owner.website} />
            <Field label="Tier" value={owner.target_tier} />
            <Field label="Relationship" value={owner.relationship_strength} />
            <Field label="Last Contact" value={fmt.date(owner.last_contact_date)} />
            <Field label="Next Follow-up" value={fmt.date(owner.next_followup_date)} />
          </dl>
          {owner.aliases && owner.aliases.length > 1 && (
            <div>
              <p className="text-xs text-gray-500 mb-1">Known as</p>
              <div className="flex flex-wrap gap-1">
                {owner.aliases.map(a => <span key={a} className="text-xs bg-gray-100 rounded px-2 py-0.5">{a}</span>)}
              </div>
            </div>
          )}
        </div>

        {/* Portfolio summary */}
        {portfolio && (
          <div className="md:col-span-2 space-y-4">
            {/* Maturity ladder */}
            <div className="bg-white rounded-lg border border-gray-200 p-4">
              <h2 className="font-semibold text-gray-800 text-sm mb-3">Maturity Ladder</h2>
              <div className="flex gap-2">
                {Object.entries(portfolio.summary.maturity_ladder).map(([bucket, count]: any) => (
                  <div key={bucket} className="flex-1 text-center">
                    <div className={`rounded p-2 text-lg font-bold ${count > 0 ? "bg-orange-50 text-orange-700" : "bg-gray-50 text-gray-400"}`}>
                      {count}
                    </div>
                    <p className="text-xs text-gray-500 mt-1">{bucket}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Properties list */}
            <div className="bg-white rounded-lg border border-gray-200 p-4">
              <h2 className="font-semibold text-gray-800 text-sm mb-3">
                Portfolio — {portfolio.summary.total_properties} Properties
              </h2>
              <div className="space-y-3">
                {portfolio.properties.map((p: any) => (
                  <div key={p.id} className="border-b border-gray-100 pb-3 last:border-0">
                    <div className="flex items-center gap-2 mb-1">
                      <Building2 className="w-3.5 h-3.5 text-gray-400 flex-shrink-0" />
                      <Link href={`/properties/${p.id}`} className="text-sm font-medium text-blue-600 hover:underline flex-1 truncate">
                        {p.name}
                      </Link>
                      <span className="text-xs text-gray-500">{p.city}, {p.state}</span>
                      {p.building_class && (
                        <span className="text-xs bg-gray-100 px-1.5 py-0.5 rounded">{p.building_class}</span>
                      )}
                      <span className="text-xs text-gray-500">{fmt.number(p.units)} units</span>
                    </div>
                    {p.loans.map((l: any) => (
                      <Link key={l.id} href={`/loans/${l.id}`}
                        className="ml-5 flex items-center gap-2 text-xs text-gray-600 hover:text-blue-600 py-0.5">
                        <FileText className="w-3 h-3" />
                        <span className="flex-1">{l.lender || "Loan"}</span>
                        <span>{fmt.date(l.maturity_date)}</span>
                        <MaturityBadge months={l.months_to_maturity !== undefined ? l.months_to_maturity : null} />
                        <span className="font-medium">{fmt.currency(l.original_amount)}</span>
                      </Link>
                    ))}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Notes */}
      <div className="bg-white rounded-lg border border-gray-200 p-5">
        <NoteEditor entityType="owner" entityId={id} />
      </div>
    </div>
  );
}

function InfoCard({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div className={`rounded-lg border p-3 ${highlight ? "border-orange-300 bg-orange-50" : "border-gray-200 bg-white"}`}>
      <p className="text-xs text-gray-500 mb-0.5">{label}</p>
      <p className="font-bold text-xl text-gray-900">{value}</p>
    </div>
  );
}

function Field({ label, value }: { label: string; value: string | null | undefined }) {
  return (
    <div className="flex gap-2">
      <dt className="text-xs text-gray-500 w-28 flex-shrink-0">{label}</dt>
      <dd className="text-sm text-gray-800">{value || "—"}</dd>
    </div>
  );
}
