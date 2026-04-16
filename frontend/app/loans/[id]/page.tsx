"use client";
import { use } from "react";
import useSWR from "swr";
import Link from "next/link";
import { api, fmt } from "@/lib/api";
import { Loan } from "@/lib/types";
import { ScoreBadge } from "@/components/shared/ScoreBadge";
import { MaturityBadge } from "@/components/shared/MaturityBadge";
import { NoteEditor } from "@/components/shared/NoteEditor";
import { ArrowLeft, ExternalLink } from "lucide-react";

const fetcher = (url: string) => api.get(url).then(r => r.data);

export default function LoanDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { data: loan, isLoading } = useSWR<Loan>(`/loans/${id}`, fetcher);
  const { data: scores } = useSWR(`/scoring/results/loan/${id}`, fetcher);

  if (isLoading) return <div className="text-gray-400 p-8">Loading…</div>;
  if (!loan) return <div className="p-8 text-red-500">Loan not found</div>;

  return (
    <div className="max-w-5xl space-y-5">
      <div className="flex items-center gap-3">
        <Link href="/loans" className="text-gray-400 hover:text-gray-700"><ArrowLeft className="w-5 h-5" /></Link>
        <h1 className="text-xl font-bold text-gray-900 flex-1 truncate">{loan.display_name || "Loan Detail"}</h1>
        <MaturityBadge months={loan.months_to_maturity} />
        <ScoreBadge score={loan.priority_score} />
      </div>

      {/* Summary cards row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <InfoCard label="Maturity Date" value={fmt.date(loan.maturity_date)} highlight={loan.months_to_maturity != null && loan.months_to_maturity < 12} />
        <InfoCard label="Original Amount" value={fmt.currency(loan.original_amount)} />
        <InfoCard label="Current Balance" value={fmt.currency(loan.current_balance)} />
        <InfoCard label="Rate / Coupon" value={`${loan.rate_type || "—"} / ${fmt.coupon(loan.coupon)}`} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* Left column: loan details */}
        <div className="bg-white rounded-lg border border-gray-200 p-5 space-y-4">
          <h2 className="font-semibold text-gray-800">Loan Details</h2>
          <dl className="space-y-2">
            <Field label="Lender" value={loan.lender} />
            <Field label="Originator" value={loan.originator} />
            <Field label="Servicer" value={loan.servicer} />
            <Field label="Origination Date" value={fmt.date(loan.origination_date)} />
            <Field label="Maturity Date" value={fmt.date(loan.maturity_date)} />
            <Field label="Loan Type" value={loan.loan_type} />
            <Field label="IO Flag" value={loan.io_flag === true ? "Interest Only" : loan.io_flag === false ? "Amortizing" : "—"} />
            <Field label="Amortization (yrs)" value={loan.amortization != null ? String(loan.amortization) : null} />
            <Field label="Term (months)" value={loan.term != null ? String(loan.term) : null} />
            <Field label="Recourse" value={loan.recourse === true ? "Yes" : loan.recourse === false ? "No" : "—"} />
            <Field label="Prepay Structure" value={loan.prepay_structure} />
            <Field label="Source" value={loan.source_precedence} />
          </dl>
        </div>

        {/* Right column: linked entities */}
        <div className="space-y-4">
          {loan.property_id && (
            <div className="bg-white rounded-lg border border-gray-200 p-4">
              <h2 className="font-semibold text-gray-800 mb-2 text-sm">Property</h2>
              <Link href={`/properties/${loan.property_id}`}
                className="text-blue-600 hover:underline font-medium flex items-center gap-1">
                {loan.property_name} <ExternalLink className="w-3.5 h-3.5" />
              </Link>
              <p className="text-xs text-gray-500">{loan.property_city}, {loan.property_state}</p>
            </div>
          )}
          {loan.owner_id && (
            <div className="bg-white rounded-lg border border-gray-200 p-4">
              <h2 className="font-semibold text-gray-800 mb-2 text-sm">Owner / Sponsor</h2>
              <Link href={`/owners/${loan.owner_id}`}
                className="text-blue-600 hover:underline font-medium flex items-center gap-1">
                {loan.owner_name} <ExternalLink className="w-3.5 h-3.5" />
              </Link>
            </div>
          )}

          {/* Score breakdown */}
          {scores && scores.length > 0 && (
            <div className="bg-white rounded-lg border border-gray-200 p-4">
              <h2 className="font-semibold text-gray-800 mb-3 text-sm">Score Breakdown</h2>
              <div className="space-y-2">
                {Object.entries(scores[0].factor_scores).map(([factor, score]: any) => (
                  <div key={factor} className="flex items-center gap-2">
                    <span className="text-xs text-gray-500 flex-1 capitalize">{factor.replace(/_/g, " ")}</span>
                    <div className="flex-1 bg-gray-100 rounded-full h-1.5">
                      <div className="h-1.5 rounded-full bg-blue-500" style={{ width: `${score}%` }} />
                    </div>
                    <span className="text-xs font-medium w-6 text-right">{Math.round(score)}</span>
                  </div>
                ))}
              </div>
              <p className="mt-2 text-xs text-gray-400">Computed: {new Date(scores[0].computed_at).toLocaleDateString()}</p>
            </div>
          )}

          {/* Provenance */}
          {loan.provenance && (
            <div className="bg-gray-50 rounded-lg border border-gray-200 p-4">
              <h2 className="font-semibold text-gray-700 mb-2 text-sm">Data Provenance</h2>
              <dl className="grid grid-cols-2 gap-x-4 gap-y-1">
                {Object.entries(loan.provenance).map(([field, source]) => (
                  <div key={field} className="flex gap-1">
                    <dt className="text-xs text-gray-500 capitalize">{field.replace(/_/g, " ")}:</dt>
                    <dd className="text-xs text-gray-700 font-medium">{source as string}</dd>
                  </div>
                ))}
              </dl>
            </div>
          )}
        </div>
      </div>

      {/* Notes */}
      <div className="bg-white rounded-lg border border-gray-200 p-5">
        <NoteEditor entityType="loan" entityId={id} />
      </div>
    </div>
  );
}

function InfoCard({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div className={`rounded-lg border p-3 ${highlight ? "border-red-300 bg-red-50" : "border-gray-200 bg-white"}`}>
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
