"""
PMSS Database Setup Script
Creates all required tables in Supabase if they don't exist.
Run this once to initialize the database schema.
"""
import sys
import os
from pathlib import Path

# Fix Windows console encoding
if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, str(Path(__file__).resolve().parent))

from backend.config import settings
from supabase import create_client


def setup_database():
    """
    Verify database connectivity and check that required tables exist.
    
    Note: Supabase tables are typically created via the Supabase Dashboard
    SQL Editor. This script verifies connectivity and lists existing tables.
    """
    print("=" * 60)
    print("  PMSS Database Setup")
    print(f"  URL: {settings.SUPABASE_URL}")
    print("=" * 60)

    client = create_client(settings.SUPABASE_URL, settings.supabase_key)

    # Required tables
    required_tables = [
        "equipment",
        "location",
        "sensor",
        "sensor_reading",
        "failure_prediction",
        "maintenance_task",
        "maintenance_log",
        "schedule",
        "technician",
        "supervisor",
        "certification",
        "resource",
        "storage_bin",
        "risk_score",
        "facility_manager",
    ]

    print("\nChecking tables...")
    existing = []
    missing = []

    for table in required_tables:
        try:
            result = client.table(table).select("*").limit(1).execute()
            count_result = client.table(table).select("*", count="exact").execute()
            row_count = count_result.count if count_result.count is not None else len(count_result.data or [])
            existing.append(table)
            print(f"  ✅ {table:<25s} ({row_count} rows)")
        except Exception as e:
            missing.append(table)
            print(f"  ❌ {table:<25s} (missing or error: {str(e)[:60]})")

    print(f"\n{'=' * 60}")
    print(f"  Found: {len(existing)}/{len(required_tables)} tables")

    if missing:
        print(f"\n  ⚠️  Missing tables: {', '.join(missing)}")
        print(f"\n  To create missing tables, run this SQL in Supabase Dashboard:")
        print(f"  (Dashboard → SQL Editor → New Query)")
        print()
        print_create_sql(missing)
    else:
        print(f"\n  ✅ All tables exist! Database is ready.")

    # Check for equipment with sensors
    try:
        eq_result = client.table("equipment").select("equipment_id, name, status").execute()
        equipment = eq_result.data or []
        print(f"\n  Equipment ({len(equipment)}):")
        for eq in equipment:
            status_icon = {"operational": "🟢", "warning": "🟡", "critical": "🔴"}.get(eq.get("status", ""), "⚫")
            print(f"    {status_icon} {eq['name']} ({eq['equipment_id'][:8]}...)")
    except:
        pass

    print()
    return len(missing) == 0


def print_create_sql(missing_tables: list[str]):
    """Print SQL statements to create missing tables."""
    sql_templates = {
        "location": """
CREATE TABLE IF NOT EXISTS location (
    location_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    address TEXT,
    facility_details TEXT
);""",
        "equipment": """
CREATE TABLE IF NOT EXISTS equipment (
    equipment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    type TEXT,
    location_id UUID REFERENCES location(location_id),
    health INTEGER DEFAULT 100,
    sensors INTEGER DEFAULT 0,
    installation_date DATE,
    warranty_end DATE,
    warranty_provider TEXT,
    status TEXT DEFAULT 'operational'
);""",
        "sensor": """
CREATE TABLE IF NOT EXISTS sensor (
    sensor_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    equipment_id UUID REFERENCES equipment(equipment_id),
    sensor_type TEXT NOT NULL,
    unit TEXT,
    threshold_min NUMERIC,
    threshold_max NUMERIC
);""",
        "sensor_reading": """
CREATE TABLE IF NOT EXISTS sensor_reading (
    reading_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sensor_id UUID REFERENCES sensor(sensor_id),
    equipment_id UUID REFERENCES equipment(equipment_id),
    machine_name TEXT,
    temperature NUMERIC,
    vibration NUMERIC,
    pressure NUMERIC,
    humidity NUMERIC,
    rpm NUMERIC,
    operational_hours NUMERIC,
    failure_probability NUMERIC,
    rul_hours NUMERIC,
    risk_level TEXT DEFAULT 'normal',
    recorded_at TIMESTAMPTZ DEFAULT now()
);""",
        "failure_prediction": """
CREATE TABLE IF NOT EXISTS failure_prediction (
    prediction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    equipment_id UUID REFERENCES equipment(equipment_id),
    predicted_failure_date DATE,
    confidence_score NUMERIC,
    affected_component TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);""",
        "supervisor": """
CREATE TABLE IF NOT EXISTS supervisor (
    supervisor_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    contact TEXT
);""",
        "technician": """
CREATE TABLE IF NOT EXISTS technician (
    technician_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    role TEXT,
    specialization TEXT,
    contact TEXT,
    location_id UUID REFERENCES location(location_id),
    supervisor_id UUID REFERENCES supervisor(supervisor_id)
);""",
        "certification": """
CREATE TABLE IF NOT EXISTS certification (
    cert_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    technician_id UUID REFERENCES technician(technician_id),
    cert_name TEXT NOT NULL,
    issued_date DATE,
    expiry_date DATE
);""",
        "maintenance_task": """
CREATE TABLE IF NOT EXISTS maintenance_task (
    task_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    equipment_id UUID REFERENCES equipment(equipment_id),
    task_type TEXT,
    priority TEXT DEFAULT 'medium',
    estimated_duration NUMERIC,
    required_skills TEXT,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);""",
        "schedule": """
CREATE TABLE IF NOT EXISTS schedule (
    schedule_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID REFERENCES maintenance_task(task_id),
    technician_id UUID REFERENCES technician(technician_id),
    supervisor_id UUID REFERENCES supervisor(supervisor_id),
    start_time TIMESTAMPTZ,
    end_time TIMESTAMPTZ,
    status TEXT DEFAULT 'pending'
);""",
        "maintenance_log": """
CREATE TABLE IF NOT EXISTS maintenance_log (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID REFERENCES maintenance_task(task_id),
    equipment_id UUID REFERENCES equipment(equipment_id),
    technician_id UUID REFERENCES technician(technician_id),
    work_description TEXT,
    outcome_status TEXT,
    log_timestamp TIMESTAMPTZ DEFAULT now()
);""",
        "risk_score": """
CREATE TABLE IF NOT EXISTS risk_score (
    risk_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID REFERENCES maintenance_task(task_id),
    score NUMERIC,
    calculated_at TIMESTAMPTZ DEFAULT now()
);""",
        "storage_bin": """
CREATE TABLE IF NOT EXISTS storage_bin (
    bin_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    location_description TEXT,
    capacity INTEGER DEFAULT 100
);""",
        "resource": """
CREATE TABLE IF NOT EXISTS resource (
    resource_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    type TEXT,
    quantity INTEGER DEFAULT 0,
    min_stock INTEGER DEFAULT 0,
    max_stock INTEGER DEFAULT 100,
    unit TEXT DEFAULT 'units',
    unit_price NUMERIC DEFAULT 0,
    bin_id UUID REFERENCES storage_bin(bin_id)
);""",
        "facility_manager": """
CREATE TABLE IF NOT EXISTS facility_manager (
    manager_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    contact TEXT,
    location_id UUID REFERENCES location(location_id)
);""",
    }

    for table in missing_tables:
        if table in sql_templates:
            print(sql_templates[table])


def seed_equipment():
    """
    Seed the database with equipment that matches the simulator profiles.
    Only inserts if equipment doesn't already exist.
    """
    from simulator.machine_profiles import get_profiles as _get_profiles
    client = create_client(settings.SUPABASE_URL, settings.supabase_key)

    profiles = _get_profiles()

    # Check if equipment exists
    existing = client.table("equipment").select("equipment_id").execute()
    existing_ids = {e["equipment_id"] for e in (existing.data or [])}

    # Ensure at least one location exists
    loc_result = client.table("location").select("location_id").limit(1).execute()
    if not loc_result.data:
        print("  Creating default location...")
        client.table("location").insert({
            "location_id": "00000000-0000-0000-0000-000000000001",
            "name": "Main Plant A",
            "address": "Industrial Zone, Block A",
        }).execute()
        client.table("location").insert({
            "location_id": "00000000-0000-0000-0000-000000000002",
            "name": "Plant B - Heavy Machinery",
            "address": "Industrial Zone, Block B",
        }).execute()
        client.table("location").insert({
            "location_id": "00000000-0000-0000-0000-000000000003",
            "name": "Plant C - Assembly",
            "address": "Industrial Zone, Block C",
        }).execute()
        client.table("location").insert({
            "location_id": "00000000-0000-0000-0000-000000000004",
            "name": "Plant D - Packaging",
            "address": "Industrial Zone, Block D",
        }).execute()

    location_ids = [
        "00000000-0000-0000-0000-000000000001",
        "00000000-0000-0000-0000-000000000002",
        "00000000-0000-0000-0000-000000000003",
        "00000000-0000-0000-0000-000000000004",
    ]

    inserted = 0
    for i, profile in enumerate(profiles):
        eq_id = profile["equipment_id"]
        if eq_id in existing_ids:
            print(f"  ⏭️  {profile['machine_name']} already exists")
            continue

        loc_id = location_ids[i % len(location_ids)]
        try:
            client.table("equipment").insert({
                "equipment_id": eq_id,
                "name": profile["machine_name"],
                "type": profile["machine_type"],
                "location_id": loc_id,
                "status": "operational",
            }).execute()

            # Create sensor for this equipment
            client.table("sensor").insert({
                "sensor_id": profile["sensor_id"],
                "equipment_id": eq_id,
                "sensor_type": "multi-sensor",
                "unit": "mixed",
            }).execute()

            print(f"  ✅ Inserted {profile['machine_name']}")
            inserted += 1
        except Exception as e:
            print(f"  ⚠️  Error inserting {profile['machine_name']}: {e}")

    print(f"\n  Seeded {inserted} new equipment entries.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="PMSS Database Setup")
    parser.add_argument("--seed", action="store_true", help="Seed equipment data")
    args = parser.parse_args()

    ready = setup_database()

    if args.seed:
        print("\nSeeding equipment data...")
        seed_equipment()

    if ready:
        print("✅ Database is ready for PMSS!")
    else:
        print("⚠️  Some tables are missing. Create them using the SQL above.")
