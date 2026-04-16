"use client";
import { use } from "react";
import useSWR from "swr";
import Link from "next/link";
import { api, fmt } from "@/lib/api";
import { Property } from "@/lib/types";
import { ScoreBadge } from "@/components/shared/ScoreBadge";
import { MaturityBadge } from "@/components/shared/MaturityBadge";
import { NoteEditor } from "@/components/shared/NoteEditor";
import { ArrowLeft } from "lucide-react";

const fetcher = (url: string) => api.get(url).then(r => r.data);

export default function PropertyDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { data: prop, isLoading } = useSWR<Property>(`/properties/${id}`, fetcher);

  if (isLoading) return <div className="text-gray-400 p-8">Loading…</div>;
  if (!prop) return <div className="p-8 text-red-500">Property not found</div>;

  return (
    <div className="max-w-5xl space-y-5">
      <div className="flex items-center gap-3">
        <Link href="/properties" className="text-gray-400 hover:text-gray-700"><ArrowLeft className="w-5 h-5" /></Link>
        <h1 className="text-xl font-bold text-gray-900 flex-1">{prop.display_name}</h1>
        <ScoreBadge score={prop.priority_score} />
      </div>

      {/* Cards row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <InfoCard label="Units" value={fmt.number(prop.units)} />
        <InfoCard label="Building Class" value={prop.building_class || "—"} />
        <InfoCard label="Year Built" value={prop.year_built ? String(prop.year_built) : "—"} />
        <InfoCard label="Occupancy" value={prop.occupancy != null ? `${(prop.occupancy * 100).toFixed(1)}%` : "—"} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* Property details */}
        <div className="bg-white rounded-lg border border-gray-200 p-5 space-y-3">
          <h2 className="font-semibold text-gray-800">Property Details</h2>
          <dl className="space-y-2">
            <Field label="Address" value={prop.canonical_address} />
            <Field label="City" value={prop.city} />
            <Field label="County" value={prop.county} />
            <Field label="State" value={prop.state} />
            <Field label="Zip" value={prop.zip} />
            <Field label="Submarket" value={prop.submarket} />
            <Field label="Property Type" value={prop.property_type} />
            <Field label="Year Renovated" value={prop.renovated_year ? String(prop.renovated_year) : null} />
            <Field label="Vacancy" value={prop.vacancy != null ? `${(prop.vacancy * 100).toFixed(1)}%` : null} />
            <Field label="Last Sale Date" value={fmt.date(prop.last_sale_date)} />
            <Field label="Last Sale Price" value={fmt.currency(prop.last_sale_price)} />
            {prop.latitude && <Field label="Coordinates" value={`${prop.latitude.toFixed(4)}, ${prop.longitude?.toFixed(4)}`} />}
          </dl>
          {prop.aliases && prop.aliases.length > 1 && (
            <div>
              <p className="text-xs text-gray-500 mb-1">Known as</p>
              <div className="flex flex-wrap gap-1">
                {prop.aliases.map(a => <span key={a} className="text-xs bg-gray-100 rounded px-2 py-0.5">{a}</span>)}
              </div>
            </div>
          )}
        </div>

        {/* Right: owner + loans */}
        <div className="space-y-4">
          {prop.owner_id && (
            <div className="bg-white rounded-lg border border-gray-200 p-4">
              <h2 className="font-semibold text-gray-800 mb-2 text-sm">Owner</h2>
              <Link href={`/owners/${prop.owner_id}`} className="text-blue-600 hover:underline font-medium">
                {prop.owner_name}
              </Link>
            </div>
          )}

          {prop.loans && prop.loans.length > 0 && (
            <div className="bg-white rounded-lg border border-gray-200 p-4">
              <h2 className="font-semibold text-gray-800 mb-3 text-sm">Loans ({prop.loans.length})</h2>
              <div className="space-y-2">
                {prop.loans.map(l => (
                  <Link key={l.id} href={`/loans/${l.id}`}
                    className="flex items-center gap-2 hover:bg-gray-50 rounded p-1.5">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-gray-800 truncate">{l.lender || l.display_name || "Loan"}</p>
                      <p className="text-xs text-gray-500">
                        {fmt.date(l.maturity_date)} · {fmt.currency(l.original_amount)}
                      </p>
                    </div>
                    <MaturityBadge months={l.months_to_maturity} />
                    <ScoreBadge score={l.priority_score} size="sm" />
                  </Link>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="bg-white rounded-lg border border-gray-200 p-5">
        <NoteEditor entityType="property" entityId={id} />
      </div>
    </div>
  );
}

function InfoCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-3">
      <p className="text-xs text-gray-500 mb-0.5">{label}</p>
      <p className="font-semibold text-gray-900">{value}</p>
    </div>
  );
}

function Field({ label, value }: { label: string; value: string | null | undefined }) {
  return (
    <div className="flex gap-2">
      <dt className="text-xs text-gray-500 w-36 flex-shrink-0">{label}</dt>
      <dd className="text-sm text-gray-800">{value || "—"}</dd>
    </div>
  );
}
