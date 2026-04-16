export interface Loan {
  id: string;
  display_name: string | null;
  property_id: string | null;
  property_name: string | null;
  property_city: string | null;
  property_state: string | null;
  owner_id: string | null;
  owner_name: string | null;
  lender: string | null;
  originator: string | null;
  servicer: string | null;
  origination_date: string | null;
  maturity_date: string | null;
  months_to_maturity: number | null;
  original_amount: number | null;
  current_balance: number | null;
  rate_type: string | null;
  coupon: number | null;
  io_flag: boolean | null;
  amortization: number | null;
  term: number | null;
  loan_type: string | null;
  recourse: boolean | null;
  prepay_structure: string | null;
  status: string;
  priority_score: number | null;
  source_precedence: string | null;
  internal_notes: string | null;
  created_at: string;
  updated_at: string;
  provenance?: Record<string, string>;
}

export interface Property {
  id: string;
  display_name: string;
  street: string | null;
  city: string | null;
  county: string | null;
  state: string | null;
  zip: string | null;
  submarket: string | null;
  canonical_address: string | null;
  latitude: number | null;
  longitude: number | null;
  units: number | null;
  year_built: number | null;
  renovated_year: number | null;
  building_class: string | null;
  property_type: string | null;
  occupancy: number | null;
  vacancy: number | null;
  last_sale_date: string | null;
  last_sale_price: number | null;
  owner_id: string | null;
  owner_name: string | null;
  priority_score: number | null;
  internal_notes: string | null;
  created_at: string;
  updated_at: string;
  loans?: LoanSummary[];
  aliases?: string[];
}

export interface Owner {
  id: string;
  display_name: string;
  normalized_name: string;
  ownership_type: string | null;
  hq_city: string | null;
  hq_state: string | null;
  website: string | null;
  tags: string[] | null;
  outreach_stage: string;
  last_contact_date: string | null;
  next_followup_date: string | null;
  relationship_strength: string | null;
  priority_score: number | null;
  target_tier: string | null;
  internal_notes: string | null;
  property_count: number;
  loan_count: number;
  total_units: number;
  upcoming_maturities: number;
  maturities_12mo: number;
  total_upcoming_volume: number;
  created_at: string;
  updated_at: string;
  aliases?: string[];
}

export interface LoanSummary {
  id: string;
  display_name: string | null;
  maturity_date: string | null;
  months_to_maturity: number | null;
  original_amount: number | null;
  lender: string | null;
  rate_type: string | null;
  io_flag: boolean | null;
  priority_score: number | null;
}

export interface MapPin {
  id: string;
  name: string;
  lat: number;
  lng: number;
  city: string | null;
  state: string | null;
  units: number | null;
  building_class: string | null;
  owner_id: string | null;
  priority_score: number | null;
}

export interface DashboardSummary {
  totals: {
    loans: number;
    properties: number;
    owners: number;
    original_balance: number;
  };
  maturity_counts: {
    within_6mo: number;
    within_12mo: number;
    within_24mo: number;
    within_36mo: number;
  };
  maturity_volumes: {
    within_6mo: number;
    within_12mo: number;
    within_24mo: number;
    within_36mo: number;
  };
  timeline: Array<{ month: string; count: number; volume: number }>;
  top_owners: Array<{ id: string; name: string; loan_count: number; total_volume: number }>;
  top_states: Array<{ state: string; loan_count: number; total_volume: number }>;
  top_lenders: Array<{ lender: string; count: number; volume: number }>;
}

export interface Note {
  id: string;
  entity_type: string;
  entity_id: string;
  body: string;
  created_at: string;
  updated_at: string;
}

export interface OutreachActivity {
  id: string;
  entity_type: string;
  entity_id: string;
  activity_type: string;
  contact_name: string | null;
  date: string | null;
  summary: string | null;
  created_at: string;
}

export interface Followup {
  id: string;
  entity_type: string;
  entity_id: string;
  due_date: string;
  description: string | null;
  completed: boolean;
  completed_at: string | null;
  created_at: string;
}

export interface OutreachTarget {
  id: string;
  owner_id: string | null;
  property_id: string | null;
  loan_id: string | null;
  stage: string;
  target_tier: string | null;
  last_contact_date: string | null;
  next_followup_date: string | null;
  relationship_strength: string | null;
  tags: string[] | null;
  internal_notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface PaginatedResponse<T> {
  total: number;
  page: number;
  limit: number;
  items: T[];
}

export const OUTREACH_STAGES = [
  "cold", "identified", "researched", "outreach_sent",
  "contacted", "meeting_scheduled", "active", "warm", "closed", "pass",
];

export const TARGET_TIERS = ["tier1", "tier2", "tier3"];
