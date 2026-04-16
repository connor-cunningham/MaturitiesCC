"""
Seed script: inserts 15 owners, 30 properties, 50 loans with realistic
multifamily data. Run from backend/ directory:
  python -m seed.seed_data
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datetime import date, datetime
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.core.config import settings
from app.models.canonical import CanonicalOwner, CanonicalProperty, CanonicalLoan, User
from app.models.scoring import ScoreConfig, DEFAULT_FACTOR_WEIGHTS
from app.models.crm import OutreachTarget, Note, Followup
from app.models.links import OwnerAlias, PropertyAlias
from app.core.security import hash_password

engine = create_async_engine(settings.DATABASE_URL, echo=False)
Session = async_sessionmaker(engine, expire_on_commit=False)


OWNERS = [
    {"name": "Greystar Real Estate Partners", "city": "Charleston", "state": "SC", "stage": "warm", "tier": "tier1"},
    {"name": "Aimco Apartment Income REIT", "city": "Denver", "state": "CO", "stage": "contacted", "tier": "tier1"},
    {"name": "Alliance Residential Company", "city": "Phoenix", "state": "AZ", "stage": "cold", "tier": "tier2"},
    {"name": "Wood Partners LLC", "city": "Atlanta", "state": "GA", "stage": "cold", "tier": "tier2"},
    {"name": "Cortland Management", "city": "Atlanta", "state": "GA", "stage": "outreach_sent", "tier": "tier1"},
    {"name": "AMLI Residential Properties", "city": "Chicago", "state": "IL", "stage": "cold", "tier": "tier2"},
    {"name": "Equity Residential", "city": "Chicago", "state": "IL", "stage": "contacted", "tier": "tier1"},
    {"name": "Essex Property Trust", "city": "San Mateo", "state": "CA", "stage": "cold", "tier": "tier2"},
    {"name": "NexPoint Real Estate Finance", "city": "Dallas", "state": "TX", "stage": "warm", "tier": "tier1"},
    {"name": "Harbor Group International", "city": "Norfolk", "state": "VA", "stage": "cold", "tier": "tier2"},
    {"name": "Simpson Housing Solutions", "city": "Greenwood Village", "state": "CO", "stage": "cold", "tier": "tier3"},
    {"name": "Berkshire Residential Investments", "city": "Boston", "state": "MA", "stage": "researched", "tier": "tier2"},
    {"name": "Starwood Capital Group", "city": "Greenwich", "state": "CT", "stage": "cold", "tier": "tier1"},
    {"name": "Blackstone Real Estate", "city": "New York", "state": "NY", "stage": "researched", "tier": "tier1"},
    {"name": "KKR Real Estate Finance Trust", "city": "New York", "state": "NY", "stage": "cold", "tier": "tier2"},
]

PROPERTIES = [
    # Greystar (owner index 0) — 4 properties
    {"name": "The Monarch at Midtown", "street": "1200 Peachtree St NE", "city": "Atlanta", "state": "GA", "zip": "30309", "units": 320, "class": "A", "year": 2018, "lat": 33.7874, "lng": -84.3839, "owner_idx": 0},
    {"name": "Greystar at Uptown", "street": "2500 McKinney Ave", "city": "Dallas", "state": "TX", "zip": "75201", "units": 280, "class": "A", "year": 2019, "lat": 32.8036, "lng": -96.7970, "owner_idx": 0},
    {"name": "Venue at Midtown Houston", "street": "4300 Main St", "city": "Houston", "state": "TX", "zip": "77002", "units": 240, "class": "B", "year": 2015, "lat": 29.7183, "lng": -95.3786, "owner_idx": 0},
    {"name": "The Retreat at Buckhead", "street": "3100 Piedmont Rd NE", "city": "Atlanta", "state": "GA", "zip": "30305", "units": 180, "class": "A", "year": 2020, "lat": 33.8390, "lng": -84.3625, "owner_idx": 0},
    # Aimco (index 1) — 3 properties
    {"name": "Palazzo East at Park La Brea", "street": "6245 W 3rd St", "city": "Los Angeles", "state": "CA", "zip": "90036", "units": 350, "class": "A", "year": 2017, "lat": 34.0702, "lng": -118.3574, "owner_idx": 1},
    {"name": "Hamilton on the Bay", "street": "555 NE 34th St", "city": "Miami", "state": "FL", "zip": "33137", "units": 271, "class": "A", "year": 2021, "lat": 25.8111, "lng": -80.1878, "owner_idx": 1},
    {"name": "One Canal Street", "street": "1 Canal St", "city": "Boston", "state": "MA", "zip": "02114", "units": 310, "class": "A", "year": 2016, "lat": 42.3625, "lng": -71.0532, "owner_idx": 1},
    # Alliance (index 2) — 3 properties
    {"name": "Broadstone Old Town", "street": "1500 N Wells St", "city": "Chicago", "state": "IL", "zip": "60610", "units": 196, "class": "B", "year": 2014, "lat": 41.9123, "lng": -87.6351, "owner_idx": 2},
    {"name": "Broadstone Midtown", "street": "900 W Peachtree St NE", "city": "Atlanta", "state": "GA", "zip": "30309", "units": 225, "class": "B", "year": 2013, "lat": 33.7876, "lng": -84.3870, "owner_idx": 2},
    {"name": "Broadstone Solis", "street": "3200 Richmond Ave", "city": "Houston", "state": "TX", "zip": "77098", "units": 150, "class": "B", "year": 2012, "lat": 29.7413, "lng": -95.4348, "owner_idx": 2},
    # Wood Partners (index 3) — 2 properties
    {"name": "Alta Midtown", "street": "1800 Monroe Dr NE", "city": "Atlanta", "state": "GA", "zip": "30324", "units": 290, "class": "A", "year": 2020, "lat": 33.8025, "lng": -84.3695, "owner_idx": 3},
    {"name": "Alta Domain", "street": "11501 Rock Rose Ave", "city": "Austin", "state": "TX", "zip": "78758", "units": 340, "class": "A", "year": 2019, "lat": 30.4011, "lng": -97.7230, "owner_idx": 3},
    # Cortland (index 4) — 3 properties
    {"name": "Cortland Midtown West", "street": "450 W 33rd St", "city": "New York", "state": "NY", "zip": "10001", "units": 400, "class": "A", "year": 2022, "lat": 40.7488, "lng": -73.9974, "owner_idx": 4},
    {"name": "Cortland Southpark", "street": "6800 Morrison Blvd", "city": "Charlotte", "state": "NC", "zip": "28211", "units": 210, "class": "A", "year": 2018, "lat": 35.1483, "lng": -80.8319, "owner_idx": 4},
    {"name": "Cortland at Vinings", "street": "2500 Vinings Pkwy SE", "city": "Smyrna", "state": "GA", "zip": "30080", "units": 170, "class": "B", "year": 2015, "lat": 33.8665, "lng": -84.5176, "owner_idx": 4},
    # AMLI (index 5) — 2 properties
    {"name": "AMLI Riverfront Park", "street": "1500 Little Raven St", "city": "Denver", "state": "CO", "zip": "80202", "units": 240, "class": "A", "year": 2016, "lat": 39.7613, "lng": -105.0052, "owner_idx": 5},
    {"name": "AMLI on 2nd", "street": "206 2nd Ave S", "city": "Seattle", "state": "WA", "zip": "98104", "units": 192, "class": "A", "year": 2017, "lat": 47.6001, "lng": -122.3353, "owner_idx": 5},
    # Equity Residential (index 6) — 2 properties
    {"name": "Equity Upper West Side", "street": "2109 Broadway", "city": "New York", "state": "NY", "zip": "10023", "units": 260, "class": "A", "year": 2018, "lat": 40.7847, "lng": -73.9817, "owner_idx": 6},
    {"name": "The Hayden", "street": "2720 Battery St", "city": "San Francisco", "state": "CA", "zip": "94123", "units": 105, "class": "A", "year": 2015, "lat": 37.8007, "lng": -122.4374, "owner_idx": 6},
    # Essex (index 7) — 2 properties
    {"name": "Essex Foxchase", "street": "6150 N 16th St", "city": "Arlington", "state": "VA", "zip": "22205", "units": 1053, "class": "B", "year": 1963, "lat": 38.8825, "lng": -77.1299, "owner_idx": 7},
    {"name": "Essex on Camden", "street": "1350 S Camden Dr", "city": "Los Angeles", "state": "CA", "zip": "90035", "units": 78, "class": "A", "year": 2014, "lat": 34.0461, "lng": -118.3888, "owner_idx": 7},
    # NexPoint (index 8) — 2 properties
    {"name": "NexPoint Multifamily Capital Trust I", "street": "11800 Lakeline Blvd", "city": "Cedar Park", "state": "TX", "zip": "78613", "units": 300, "class": "B", "year": 2010, "lat": 30.5046, "lng": -97.8195, "owner_idx": 8},
    {"name": "NexPoint Waterford", "street": "5001 Waterford Dr", "city": "Charlotte", "state": "NC", "zip": "28269", "units": 280, "class": "C", "year": 2002, "lat": 35.3203, "lng": -80.8198, "owner_idx": 8},
    # Harbor Group (index 9) — 2 properties
    {"name": "Harbor Pointe Apartments", "street": "4200 Coliseum Dr", "city": "Hampton", "state": "VA", "zip": "23666", "units": 320, "class": "B", "year": 2008, "lat": 37.0480, "lng": -76.4153, "owner_idx": 9},
    {"name": "The Reserve at Harbor Hills", "street": "8900 Harbor Hills Dr", "city": "Norfolk", "state": "VA", "zip": "23518", "units": 200, "class": "C", "year": 1998, "lat": 36.9289, "lng": -76.2405, "owner_idx": 9},
    # Simpson (index 10) — 1 property
    {"name": "Simpson Riverview Place", "street": "100 River Rd", "city": "Denver", "state": "CO", "zip": "80203", "units": 164, "class": "B", "year": 2011, "lat": 39.7205, "lng": -104.9899, "owner_idx": 10},
    # Berkshire (index 11) — 1 property
    {"name": "Berkshire Ninth and Lincoln", "street": "900 Lincoln St", "city": "Denver", "state": "CO", "zip": "80203", "units": 220, "class": "A", "year": 2017, "lat": 39.7277, "lng": -104.9853, "owner_idx": 11},
    # Starwood (index 12) — 1 property
    {"name": "Starwood Irvine Spectrum", "street": "6800 Irvine Center Dr", "city": "Irvine", "state": "CA", "zip": "92618", "units": 480, "class": "A", "year": 2020, "lat": 33.6459, "lng": -117.7433, "owner_idx": 12},
    # Blackstone (index 13) — 1 property
    {"name": "Park Place at Brambleton", "street": "42175 Park Place Dr", "city": "Ashburn", "state": "VA", "zip": "20148", "units": 350, "class": "A", "year": 2019, "lat": 39.0428, "lng": -77.4921, "owner_idx": 13},
    # KKR (index 14) — 1 property
    {"name": "KKR Lakeview Flats", "street": "1000 W Irving Park Rd", "city": "Chicago", "state": "IL", "zip": "60613", "units": 190, "class": "B", "year": 2009, "lat": 41.9531, "lng": -87.6562, "owner_idx": 14},
]

LOANS = [
    # < 6 months (very hot)
    {"prop": 0,  "lender": "Goldman Sachs Bank USA", "orig": 50_000_000, "rate": "floating", "io": True,  "maturity": date(2026, 7, 1),  "originated": date(2021, 7, 1),  "coupon": 6.25},
    {"prop": 4,  "lender": "JPMorgan Chase Bank", "orig": 72_000_000, "rate": "floating", "io": True,  "maturity": date(2026, 8, 15), "originated": date(2021, 8, 15), "coupon": 5.95},
    {"prop": 12, "lender": "Freddie Mac", "orig": 85_000_000, "rate": "fixed",    "io": False, "maturity": date(2026, 9, 1),  "originated": date(2016, 9, 1),  "coupon": 3.75},
    {"prop": 6,  "lender": "Fannie Mae",  "orig": 63_000_000, "rate": "fixed",    "io": False, "maturity": date(2026, 9, 30), "originated": date(2016, 9, 30), "coupon": 3.88},
    {"prop": 27, "lender": "Wells Fargo Bank", "orig": 45_000_000, "rate": "floating", "io": True,  "maturity": date(2026, 10, 1), "originated": date(2021, 10, 1), "coupon": 5.80},
    # 6-12 months
    {"prop": 1,  "lender": "Deutsche Bank",  "orig": 55_000_000, "rate": "floating", "io": True,  "maturity": date(2026, 11, 1), "originated": date(2021, 11, 1), "coupon": 6.10},
    {"prop": 5,  "lender": "Bank of America", "orig": 48_000_000, "rate": "fixed",   "io": False, "maturity": date(2026, 12, 1), "originated": date(2016, 12, 1), "coupon": 3.95},
    {"prop": 10, "lender": "Citibank NA",    "orig": 38_000_000, "rate": "floating", "io": True,  "maturity": date(2027, 1, 1),  "originated": date(2022, 1, 1),  "coupon": 5.50},
    {"prop": 11, "lender": "Freddie Mac",    "orig": 42_000_000, "rate": "fixed",    "io": False, "maturity": date(2027, 2, 1),  "originated": date(2017, 2, 1),  "coupon": 3.65},
    {"prop": 14, "lender": "Fannie Mae",     "orig": 28_000_000, "rate": "fixed",    "io": False, "maturity": date(2027, 3, 1),  "originated": date(2017, 3, 1),  "coupon": 3.72},
    {"prop": 16, "lender": "Morgan Stanley", "orig": 35_000_000, "rate": "floating", "io": True,  "maturity": date(2027, 3, 15), "originated": date(2022, 3, 15), "coupon": 5.75},
    {"prop": 22, "lender": "PNC Bank",       "orig": 40_000_000, "rate": "floating", "io": False, "maturity": date(2027, 4, 1),  "originated": date(2022, 4, 1),  "coupon": 5.60},
    {"prop": 23, "lender": "Truist Bank",    "orig": 30_000_000, "rate": "fixed",    "io": False, "maturity": date(2027, 4, 15), "originated": date(2017, 4, 15), "coupon": 3.90},
    {"prop": 2,  "lender": "New York Life",  "orig": 22_000_000, "rate": "fixed",    "io": False, "maturity": date(2027, 5, 1),  "originated": date(2017, 5, 1),  "coupon": 4.00},
    {"prop": 15, "lender": "Berkshire Bank", "orig": 32_000_000, "rate": "floating", "io": True,  "maturity": date(2027, 6, 1),  "originated": date(2022, 6, 1),  "coupon": 5.40},
    {"prop": 24, "lender": "KeyBank",        "orig": 18_000_000, "rate": "fixed",    "io": False, "maturity": date(2027, 6, 30), "originated": date(2017, 6, 30), "coupon": 4.05},
    # 12-24 months
    {"prop": 3,  "lender": "Freddie Mac",    "orig": 30_000_000, "rate": "fixed",    "io": False, "maturity": date(2027, 9, 1),  "originated": date(2017, 9, 1),  "coupon": 3.80},
    {"prop": 7,  "lender": "Fannie Mae",     "orig": 27_000_000, "rate": "fixed",    "io": False, "maturity": date(2027, 10, 1), "originated": date(2017, 10, 1), "coupon": 3.70},
    {"prop": 8,  "lender": "Wells Fargo",    "orig": 20_000_000, "rate": "floating", "io": True,  "maturity": date(2027, 11, 1), "originated": date(2022, 11, 1), "coupon": 5.30},
    {"prop": 9,  "lender": "CBRE Capital",   "orig": 15_000_000, "rate": "fixed",    "io": False, "maturity": date(2027, 12, 1), "originated": date(2017, 12, 1), "coupon": 3.95},
    {"prop": 13, "lender": "Bank of America","orig": 38_000_000, "rate": "floating", "io": True,  "maturity": date(2028, 1, 1),  "originated": date(2023, 1, 1),  "coupon": 5.20},
    {"prop": 17, "lender": "Goldman Sachs",  "orig": 55_000_000, "rate": "floating", "io": True,  "maturity": date(2028, 2, 1),  "originated": date(2023, 2, 1),  "coupon": 5.15},
    {"prop": 18, "lender": "JPMorgan Chase", "orig": 18_000_000, "rate": "fixed",    "io": False, "maturity": date(2028, 3, 1),  "originated": date(2018, 3, 1),  "coupon": 4.25},
    {"prop": 19, "lender": "Freddie Mac",    "orig": 80_000_000, "rate": "fixed",    "io": False, "maturity": date(2028, 4, 1),  "originated": date(2018, 4, 1),  "coupon": 4.15},
    {"prop": 20, "lender": "Fannie Mae",     "orig": 14_000_000, "rate": "fixed",    "io": False, "maturity": date(2028, 5, 1),  "originated": date(2018, 5, 1),  "coupon": 4.10},
    {"prop": 21, "lender": "Citibank",       "orig": 42_000_000, "rate": "floating", "io": True,  "maturity": date(2028, 6, 1),  "originated": date(2023, 6, 1),  "coupon": 5.05},
    {"prop": 25, "lender": "KeyBank",        "orig": 25_000_000, "rate": "floating", "io": True,  "maturity": date(2028, 7, 1),  "originated": date(2023, 7, 1),  "coupon": 5.00},
    {"prop": 26, "lender": "Berkshire Bank", "orig": 28_000_000, "rate": "fixed",    "io": False, "maturity": date(2028, 8, 1),  "originated": date(2018, 8, 1),  "coupon": 4.50},
    {"prop": 28, "lender": "Truist Bank",    "orig": 58_000_000, "rate": "fixed",    "io": False, "maturity": date(2028, 9, 1),  "originated": date(2018, 9, 1),  "coupon": 4.30},
    {"prop": 29, "lender": "Morgan Stanley", "orig": 32_000_000, "rate": "floating", "io": True,  "maturity": date(2028, 10, 1), "originated": date(2023, 10, 1), "coupon": 4.95},
    # 24-36 months
    {"prop": 0,  "lender": "CBRE Capital",   "orig": 12_000_000, "rate": "fixed",    "io": False, "maturity": date(2028, 12, 1), "originated": date(2018, 12, 1), "coupon": 4.60},
    {"prop": 4,  "lender": "PNC Bank",       "orig": 22_000_000, "rate": "floating", "io": True,  "maturity": date(2029, 1, 1),  "originated": date(2024, 1, 1),  "coupon": 4.80},
    {"prop": 10, "lender": "New York Life",  "orig": 18_000_000, "rate": "fixed",    "io": False, "maturity": date(2029, 3, 1),  "originated": date(2019, 3, 1),  "coupon": 4.55},
    {"prop": 12, "lender": "Fannie Mae",     "orig": 60_000_000, "rate": "fixed",    "io": False, "maturity": date(2029, 6, 1),  "originated": date(2019, 6, 1),  "coupon": 3.55},
    {"prop": 14, "lender": "Freddie Mac",    "orig": 20_000_000, "rate": "fixed",    "io": False, "maturity": date(2029, 9, 1),  "originated": date(2019, 9, 1),  "coupon": 3.60},
    # > 36 months
    {"prop": 1,  "lender": "Wells Fargo",    "orig": 35_000_000, "rate": "fixed",    "io": False, "maturity": date(2030, 1, 1),  "originated": date(2020, 1, 1),  "coupon": 3.40},
    {"prop": 5,  "lender": "Deutsche Bank",  "orig": 48_000_000, "rate": "floating", "io": True,  "maturity": date(2030, 6, 1),  "originated": date(2025, 6, 1),  "coupon": 4.60},
    {"prop": 6,  "lender": "Citibank",       "orig": 60_000_000, "rate": "fixed",    "io": False, "maturity": date(2031, 1, 1),  "originated": date(2021, 1, 1),  "coupon": 3.20},
    {"prop": 7,  "lender": "Bank of America","orig": 24_000_000, "rate": "fixed",    "io": False, "maturity": date(2031, 7, 1),  "originated": date(2021, 7, 1),  "coupon": 3.10},
    {"prop": 9,  "lender": "JPMorgan Chase", "orig": 12_000_000, "rate": "fixed",    "io": False, "maturity": date(2032, 1, 1),  "originated": date(2022, 1, 1),  "coupon": 3.50},
    {"prop": 11, "lender": "Freddie Mac",    "orig": 35_000_000, "rate": "fixed",    "io": False, "maturity": date(2032, 6, 1),  "originated": date(2022, 6, 1),  "coupon": 3.45},
    {"prop": 13, "lender": "Fannie Mae",     "orig": 42_000_000, "rate": "fixed",    "io": False, "maturity": date(2032, 9, 1),  "originated": date(2022, 9, 1),  "coupon": 3.38},
    {"prop": 15, "lender": "Morgan Stanley", "orig": 28_000_000, "rate": "fixed",    "io": False, "maturity": date(2033, 1, 1),  "originated": date(2023, 1, 1),  "coupon": 4.75},
    {"prop": 17, "lender": "Goldman Sachs",  "orig": 50_000_000, "rate": "fixed",    "io": False, "maturity": date(2033, 7, 1),  "originated": date(2023, 7, 1),  "coupon": 5.10},
    {"prop": 19, "lender": "Wells Fargo",    "orig": 65_000_000, "rate": "fixed",    "io": False, "maturity": date(2033, 9, 1),  "originated": date(2023, 9, 1),  "coupon": 4.90},
    {"prop": 22, "lender": "PNC Bank",       "orig": 30_000_000, "rate": "fixed",    "io": False, "maturity": date(2034, 1, 1),  "originated": date(2024, 1, 1),  "coupon": 5.20},
    {"prop": 24, "lender": "KeyBank",        "orig": 14_000_000, "rate": "fixed",    "io": False, "maturity": date(2034, 6, 1),  "originated": date(2024, 6, 1),  "coupon": 5.15},
    {"prop": 26, "lender": "Truist Bank",    "orig": 20_000_000, "rate": "fixed",    "io": False, "maturity": date(2035, 1, 1),  "originated": date(2025, 1, 1),  "coupon": 5.30},
    {"prop": 28, "lender": "CBRE Capital",   "orig": 45_000_000, "rate": "fixed",    "io": False, "maturity": date(2035, 9, 1),  "originated": date(2025, 9, 1),  "coupon": 5.45},
    {"prop": 29, "lender": "New York Life",  "orig": 25_000_000, "rate": "fixed",    "io": False, "maturity": date(2036, 1, 1),  "originated": date(2026, 1, 1),  "coupon": 5.60},
]


async def seed():
    async with Session() as session:
        # Default user
        user = User(
            username="admin",
            hashed_password=hash_password("admin123"),
            is_active=True,
            created_at=datetime.utcnow(),
        )
        session.add(user)

        # Default score config
        config = ScoreConfig(
            name="Default",
            description="Default scoring configuration",
            factor_weights=DEFAULT_FACTOR_WEIGHTS,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        session.add(config)

        # Create owners
        owner_objects = []
        for o in OWNERS:
            from app.etl.normalizers.names import normalize_owner_name
            owner = CanonicalOwner(
                display_name=o["name"],
                normalized_name=normalize_owner_name(o["name"]),
                hq_city=o["city"],
                hq_state=o["state"],
                outreach_stage=o.get("stage", "cold"),
                target_tier=o.get("tier"),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            session.add(owner)
            owner_objects.append(owner)

        await session.flush()

        # Create properties
        property_objects = []
        for p in PROPERTIES:
            owner = owner_objects[p["owner_idx"]]
            prop = CanonicalProperty(
                display_name=p["name"],
                street=p["street"],
                city=p["city"],
                state=p["state"],
                zip=p["zip"],
                units=p["units"],
                building_class=p["class"],
                year_built=p["year"],
                property_type="Multifamily",
                latitude=p.get("lat"),
                longitude=p.get("lng"),
                canonical_address=f"{p['street'].lower()}, {p['city'].lower()}, {p['state']}",
                owner_id=owner.id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            session.add(prop)
            property_objects.append(prop)

        await session.flush()

        # Create loans
        for l in LOANS:
            prop = property_objects[l["prop"]]
            loan = CanonicalLoan(
                display_name=f"{prop.display_name} — {l['lender']}",
                property_id=prop.id,
                owner_id=prop.owner_id,
                lender=l["lender"],
                origination_date=l["originated"],
                maturity_date=l["maturity"],
                original_amount=l["orig"],
                rate_type=l["rate"],
                coupon=l["coupon"],
                io_flag=l["io"],
                status="active",
                source_precedence="internal",
                provenance={"lender": "internal", "maturity_date": "internal", "original_amount": "internal"},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            session.add(loan)

        await session.flush()

        # Sample outreach targets
        for owner in owner_objects[:5]:
            target = OutreachTarget(
                owner_id=owner.id,
                stage=owner.outreach_stage or "identified",
                target_tier=owner.target_tier,
                relationship_strength="cold",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            session.add(target)

        # Sample notes
        session.add(Note(
            entity_type="owner",
            entity_id=owner_objects[0].id,
            body="Greystar is expanding aggressively in Sun Belt markets. CFO is Bob Smith — reached him via mutual connection at NMHC.",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        ))
        session.add(Note(
            entity_type="owner",
            entity_id=owner_objects[4].id,
            body="Cortland sent a mass refi inquiry to Freddie Mac Q4 last year — likely actively shopping their floating rate book.",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        ))

        # Sample followup
        session.add(Followup(
            entity_type="owner",
            entity_id=owner_objects[0].id,
            due_date=date(2026, 5, 1),
            description="Follow up on Midtown Atlanta portfolio refi discussion",
            completed=False,
            created_at=datetime.utcnow(),
        ))

        await session.commit()
        print(f"Seeded: {len(OWNERS)} owners, {len(PROPERTIES)} properties, {len(LOANS)} loans")

        # Run scoring
        from app.scoring.engine import run_scoring
        scored = await run_scoring(session)
        print(f"Scored {scored} loans")


if __name__ == "__main__":
    asyncio.run(seed())
