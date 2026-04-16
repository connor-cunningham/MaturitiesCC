"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-04-16

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("username", sa.String(200), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(500), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, default=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_users_username", "users", ["username"])

    op.create_table(
        "source_files",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("original_filename", sa.String(500), nullable=False),
        sa.Column("stored_path", sa.String(1000), nullable=False),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("file_size", sa.Integer),
        sa.Column("mime_type", sa.String(200)),
        sa.Column("sheet_count", sa.Integer),
        sa.Column("uploaded_at", sa.DateTime, nullable=False),
    )

    op.create_table(
        "import_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_file_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("source_files.id")),
        sa.Column("status", sa.String(50), nullable=False, default="pending"),
        sa.Column("mapping_config", postgresql.JSON),
        sa.Column("rows_processed", sa.Integer, default=0),
        sa.Column("rows_inserted", sa.Integer, default=0),
        sa.Column("rows_merged", sa.Integer, default=0),
        sa.Column("rows_skipped", sa.Integer, default=0),
        sa.Column("rows_queued", sa.Integer, default=0),
        sa.Column("errors", postgresql.JSON),
        sa.Column("notes", sa.Text),
        sa.Column("started_at", sa.DateTime),
        sa.Column("finished_at", sa.DateTime),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )

    op.create_table(
        "canonical_owners",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("normalized_name", sa.String(500), nullable=False),
        sa.Column("display_name", sa.String(500), nullable=False),
        sa.Column("parent_company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("canonical_owners.id")),
        sa.Column("ownership_type", sa.String(100)),
        sa.Column("hq_city", sa.String(200)),
        sa.Column("hq_state", sa.String(50)),
        sa.Column("website", sa.String(500)),
        sa.Column("tags", postgresql.JSON),
        sa.Column("outreach_stage", sa.String(100), default="cold"),
        sa.Column("last_contact_date", sa.Date),
        sa.Column("next_followup_date", sa.Date),
        sa.Column("relationship_strength", sa.String(50)),
        sa.Column("priority_score", sa.Float),
        sa.Column("target_tier", sa.String(50)),
        sa.Column("internal_notes", sa.Text),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_canonical_owners_normalized_name", "canonical_owners", ["normalized_name"])

    op.create_table(
        "canonical_properties",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("display_name", sa.String(500), nullable=False),
        sa.Column("street", sa.String(500)),
        sa.Column("city", sa.String(200)),
        sa.Column("county", sa.String(200)),
        sa.Column("state", sa.String(50)),
        sa.Column("zip", sa.String(20)),
        sa.Column("submarket", sa.String(200)),
        sa.Column("canonical_address", sa.String(1000)),
        sa.Column("latitude", sa.Float),
        sa.Column("longitude", sa.Float),
        sa.Column("units", sa.Integer),
        sa.Column("year_built", sa.Integer),
        sa.Column("renovated_year", sa.Integer),
        sa.Column("building_class", sa.String(10)),
        sa.Column("property_type", sa.String(100)),
        sa.Column("occupancy", sa.Float),
        sa.Column("vacancy", sa.Float),
        sa.Column("last_sale_date", sa.Date),
        sa.Column("last_sale_price", sa.Float),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("canonical_owners.id")),
        sa.Column("priority_score", sa.Float),
        sa.Column("internal_notes", sa.Text),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_canonical_properties_city", "canonical_properties", ["city"])
    op.create_index("ix_canonical_properties_state", "canonical_properties", ["state"])

    op.create_table(
        "canonical_loans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("display_name", sa.String(500)),
        sa.Column("property_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("canonical_properties.id")),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("canonical_owners.id")),
        sa.Column("lender", sa.String(500)),
        sa.Column("originator", sa.String(500)),
        sa.Column("servicer", sa.String(500)),
        sa.Column("origination_date", sa.Date),
        sa.Column("maturity_date", sa.Date),
        sa.Column("original_amount", sa.Float),
        sa.Column("current_balance", sa.Float),
        sa.Column("rate_type", sa.String(50)),
        sa.Column("coupon", sa.Float),
        sa.Column("io_flag", sa.Boolean),
        sa.Column("amortization", sa.Integer),
        sa.Column("term", sa.Integer),
        sa.Column("loan_type", sa.String(100)),
        sa.Column("recourse", sa.Boolean),
        sa.Column("prepay_structure", sa.String(200)),
        sa.Column("status", sa.String(50), default="active"),
        sa.Column("source_precedence", sa.String(50)),
        sa.Column("provenance", postgresql.JSON),
        sa.Column("priority_score", sa.Float),
        sa.Column("internal_notes", sa.Text),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_canonical_loans_maturity_date", "canonical_loans", ["maturity_date"])

    op.create_table(
        "raw_loan_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("import_run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("import_runs.id"), nullable=False),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("row_index", sa.Integer),
        sa.Column("raw_data", postgresql.JSON, nullable=False),
        sa.Column("normalized_data", postgresql.JSON),
        sa.Column("canonical_loan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("canonical_loans.id")),
        sa.Column("match_confidence", sa.Float),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )

    op.create_table(
        "raw_property_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("import_run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("import_runs.id"), nullable=False),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("row_index", sa.Integer),
        sa.Column("raw_data", postgresql.JSON, nullable=False),
        sa.Column("normalized_data", postgresql.JSON),
        sa.Column("canonical_property_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("canonical_properties.id")),
        sa.Column("match_confidence", sa.Float),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )

    op.create_table(
        "raw_owner_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("import_run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("import_runs.id"), nullable=False),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("row_index", sa.Integer),
        sa.Column("raw_data", postgresql.JSON, nullable=False),
        sa.Column("normalized_data", postgresql.JSON),
        sa.Column("canonical_owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("canonical_owners.id")),
        sa.Column("match_confidence", sa.Float),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )

    op.create_table(
        "owner_aliases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("canonical_owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("canonical_owners.id"), nullable=False),
        sa.Column("alias_name", sa.String(500), nullable=False),
        sa.Column("normalized_alias", sa.String(500), nullable=False),
        sa.Column("source_type", sa.String(50)),
        sa.Column("import_run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("import_runs.id")),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_owner_aliases_normalized_alias", "owner_aliases", ["normalized_alias"])

    op.create_table(
        "property_aliases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("canonical_property_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("canonical_properties.id"), nullable=False),
        sa.Column("alias_name", sa.String(500), nullable=False),
        sa.Column("normalized_alias", sa.String(500), nullable=False),
        sa.Column("source_type", sa.String(50)),
        sa.Column("import_run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("import_runs.id")),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_property_aliases_normalized_alias", "property_aliases", ["normalized_alias"])

    op.create_table(
        "loan_source_mappings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("canonical_loan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("canonical_loans.id"), nullable=False),
        sa.Column("raw_loan_record_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("raw_loan_records.id"), nullable=False),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("field_provenance", postgresql.JSON),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )

    op.create_table(
        "match_candidates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("candidate_a_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("candidate_b_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("confidence", sa.Float, nullable=False),
        sa.Column("match_reasons", postgresql.JSON),
        sa.Column("status", sa.String(50), default="pending"),
        sa.Column("import_run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("import_runs.id")),
        sa.Column("resolved_at", sa.DateTime),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )

    op.create_table(
        "manual_match_overrides",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("canonical_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reason", sa.Text),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )

    op.create_table(
        "notes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_notes_entity_id", "notes", ["entity_id"])

    op.create_table(
        "outreach_activities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("activity_type", sa.String(100), nullable=False),
        sa.Column("contact_name", sa.String(300)),
        sa.Column("date", sa.Date),
        sa.Column("summary", sa.Text),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_outreach_activities_entity_id", "outreach_activities", ["entity_id"])

    op.create_table(
        "followups",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("due_date", sa.Date, nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("completed", sa.Boolean, default=False),
        sa.Column("completed_at", sa.DateTime),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_followups_entity_id", "followups", ["entity_id"])

    op.create_table(
        "outreach_targets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("canonical_owners.id")),
        sa.Column("property_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("canonical_properties.id")),
        sa.Column("loan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("canonical_loans.id")),
        sa.Column("priority_score", sa.String(50)),
        sa.Column("target_tier", sa.String(50)),
        sa.Column("stage", sa.String(100), default="identified"),
        sa.Column("last_contact_date", sa.Date),
        sa.Column("next_followup_date", sa.Date),
        sa.Column("relationship_strength", sa.String(50)),
        sa.Column("tags", postgresql.JSON),
        sa.Column("internal_notes", sa.Text),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    op.create_table(
        "score_configs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("factor_weights", postgresql.JSON, nullable=False),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    op.create_table(
        "score_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("config_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("total_score", sa.Float, nullable=False),
        sa.Column("factor_scores", postgresql.JSON, nullable=False),
        sa.Column("computed_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_score_results_entity_id", "score_results", ["entity_id"])


def downgrade() -> None:
    for table in [
        "score_results", "score_configs", "outreach_targets", "followups",
        "outreach_activities", "notes", "manual_match_overrides", "match_candidates",
        "loan_source_mappings", "property_aliases", "owner_aliases",
        "raw_owner_records", "raw_property_records", "raw_loan_records",
        "canonical_loans", "canonical_properties", "canonical_owners",
        "import_runs", "source_files", "users",
    ]:
        op.drop_table(table)
