"""Sample data for the hackathon demo.

    python -m app.seed            # seed if the database is empty
    python -m app.seed --reset    # wipe everything and seed again

Demo logins (password for all: demo1234)
    patient@demo.com     Patient
    staff@demo.com       Hospital staff (Riverside General Hospital, id 1)
    ambulance@demo.com   Ambulance coordinator
    admin@demo.com       Administrator
"""
import argparse
import random
from datetime import timedelta

import numpy as np
from sqlalchemy import select

from app.database.connection import Base, engine
from app.database.session import SessionLocal
from app.models import (Ambulance, Bed, CapacityHistory, EmergencyRequest, Hospital, Patient, Referral, User)
from app.services import hospital_service as hs
from app.utils.helpers import utcnow
from app.utils.security import hash_password
from app.utils.validators import bed_prefix

DEMO_PASSWORD = "demo1234"
HISTORY_DAYS = 14
REPORT_DAYS = 28

# name, area, address, lat, lng, phone, emergency, specialties, beds{type: (total, available)}
HOSPITALS = [
    ("Riverside General Hospital", "Central District", "12 Clifton Road, Karachi", 24.8780, 67.0200, "+92 21 555 0101", "OPEN",
     ["Cardiology", "Trauma", "Neurology"],
     {"ICU": (30, 6), "General": (180, 52), "Emergency": (40, 11), "Ventilator": (24, 9), "Operation Theater": (4, 2)}),
    ("St. Mary Medical Center", "North Park", "45 North Park Avenue, Karachi", 24.8950, 67.0450, "+92 21 555 0102", "BUSY",
     ["Pediatrics", "Maternity"],
     {"ICU": (20, 2), "General": (120, 18), "Emergency": (25, 3), "Ventilator": (12, 2)}),
    ("Lakeshore Trauma Institute", "Lakeshore", "7 Lakeshore Drive, Karachi", 24.8300, 67.0800, "+92 21 555 0103", "BUSY",
     ["Trauma", "Burns", "Orthopedics"],
     {"ICU": (25, 0), "General": (90, 4), "Emergency": (30, 1), "Ventilator": (15, 0)}),
    ("Hillcrest Community Hospital", "West Hills", "3 Hillcrest Road, Karachi", 24.8450, 66.9750, "+92 21 555 0104", "OPEN",
     ["General Medicine", "Oncology"],
     {"ICU": (15, 7), "General": (140, 64), "Emergency": (20, 9), "Ventilator": (10, 6), "Operation Theater": (3, 1)}),
    ("Indus Heart & Emergency Center", "Defence", "88 Khayaban-e-Shahbaz, Karachi", 24.8700, 67.0600, "+92 21 555 0105", "OPEN",
     ["Cardiology", "Emergency Medicine"],
     {"ICU": (18, 5), "General": (60, 20), "Emergency": (20, 7), "Ventilator": (10, 4), "Operation Theater": (4, 2)}),
    ("Bayview Children's Hospital", "Seaview", "21 Seaview Road, Karachi", 24.8100, 67.0300, "+92 21 555 0106", "OPEN",
     ["Pediatrics", "Neonatology"],
     {"ICU": (12, 4), "General": (80, 30), "Emergency": (15, 6), "Ventilator": (6, 3)}),
]
NAMES = ["A. Khan", "R. Silva", "M. Osei", "S. Ahmed", "F. Noor", "I. Malik", "Z. Hussain", "N. Baig", "H. Raza",
         "T. Qureshi", "K. Shah", "L. Fernandes", "D. Ali", "U. Farooq", "B. Mirza", "Y. Iqbal"]
CONDITIONS = ["Chest pain", "Road accident, fractures", "Severe asthma attack", "Stroke symptoms", "High fever, dehydration",
              "Post-operative complications", "Respiratory distress", "Diabetic emergency", "Head injury", "Burns"]
SERVICES = ["Emergency"] * 5 + ["ICU"] * 2 + ["General"] * 2 + ["Ventilator"]


def wipe(db):
    for table in reversed(Base.metadata.sorted_tables):
        db.execute(table.delete())
    db.commit()


def make_beds(db, rng: random.Random, hospitals: list[Hospital]):
    for h, spec in zip(hospitals, HOSPITALS):
        for btype, (total, avail) in spec[-1].items():
            others = total - avail
            reserved = min(2, others // 6)
            cleaning = round(others * 0.05)
            statuses = (["Available"] * avail + ["Reserved"] * reserved + ["Cleaning"] * cleaning
                        + ["Occupied"] * (others - reserved - cleaning))
            rng.shuffle(statuses)
            prefix = bed_prefix(btype)
            for i, st in enumerate(statuses, start=1):
                db.add(Bed(hospital_id=h.hospital_id, code=f"{prefix}-{i:02d}", bed_type=btype, status=st,
                           patient_name=rng.choice(NAMES) if st == "Occupied" else None))
    db.flush()


def make_users(db, hospitals):
    pw = hash_password(DEMO_PASSWORD)
    users = [
        User(name="Demo Patient", email="patient@demo.com", password_hash=pw, role="patient"),
        User(name="Dr. Sara Khan", email="staff@demo.com", password_hash=pw, role="hospital", hospital_id=hospitals[0].hospital_id),
        User(name="Nurse Ali Raza", email="staff2@demo.com", password_hash=pw, role="hospital", hospital_id=hospitals[1].hospital_id),
        User(name="Dispatcher Omar", email="ambulance@demo.com", password_hash=pw, role="ambulance"),
        User(name="System Admin", email="admin@demo.com", password_hash=pw, role="admin"),
    ]
    db.add_all(users)
    db.flush()
    return users


def make_live_requests(db, hospitals, patient_user, now):
    """The 'right now' data that the dashboards show: pending emergencies + the demo patient's 3 referrals."""
    h1, h2, h3 = hospitals[0], hospitals[1], hospitals[2]
    live = [  # (name, age, condition, priority, service, eta, source, minutes_ago)
        ("Imran Siddiqui", 54, "Suspected cardiac arrest", "Critical", "ICU", 6, "Ambulance A-12", 8),
        ("Ayesha Tariq", 29, "Road accident, fractures", "Urgent", "Emergency", 12, "Ambulance A-07", 14),
        ("Hamza Ali", 7, "Severe asthma attack", "Urgent", "Emergency", 9, "Referral", 21),
        ("Abdul Rehman", 71, "Stroke symptoms", "Critical", "ICU", 15, "Ambulance A-03", 26),
    ]
    for name, age, cond, prio, svc, eta, src, mins in live:
        p = Patient(name=name, age=age, medical_requirement=cond, priority=prio)
        db.add(p)
        db.flush()
        db.add(EmergencyRequest(patient_id=p.patient_id, hospital_id=h1.hospital_id, required_service=svc,
                                location="Karachi", condition=cond, priority=prio, status="Pending", source=src,
                                eta_minutes=eta, created_time=now - timedelta(minutes=mins)))
    db.flush()

    me = Patient(user_id=patient_user.id, name="Demo Patient", age=34, medical_requirement="Cardiac monitoring", priority="Urgent")
    db.add(me)
    db.flush()
    reserved = db.scalar(select(Bed).where(Bed.hospital_id == h1.hospital_id, Bed.bed_type == "ICU", Bed.status == "Reserved"))
    db.add_all([
        Referral(patient_id=me.patient_id, to_hospital=h1.hospital_id, bed_id=reserved.bed_id if reserved else None,
                 bed_type="ICU", priority="Critical", status="Accepted", note="Bed reserved. Arrive within 30 minutes.",
                 created_at=now - timedelta(minutes=10), responded_at=now - timedelta(minutes=6)),
        Referral(patient_id=me.patient_id, to_hospital=h2.hospital_id, bed_type="General", priority="Normal",
                 status="Pending", note="Waiting for hospital response.", created_at=now - timedelta(minutes=35)),
        Referral(patient_id=me.patient_id, to_hospital=h3.hospital_id, bed_type="Emergency", priority="Urgent",
                 status="Rejected", note="No emergency beds available. Try another hospital.",
                 created_at=now - timedelta(hours=2), responded_at=now - timedelta(hours=2) + timedelta(minutes=9)),
    ])


def make_fleet(db, hospitals):
    db.add_all([
        Ambulance(code="A-12", crew="Crew Delta", status="En route", destination_hospital_id=hospitals[0].hospital_id, eta_minutes=6),
        Ambulance(code="A-07", crew="Crew Echo", status="On scene"),
        Ambulance(code="A-03", crew="Crew Alpha", status="En route", destination_hospital_id=hospitals[3].hospital_id, eta_minutes=15),
        Ambulance(code="A-15", crew="Crew Bravo", status="Available"),
    ])


def make_request_history(db, hospitals, np_rng, now):
    """~4 weeks of past emergencies and referrals (feeds Reports and spike detection)."""
    hour_w = np.array([2, 1, 1, 1, 1, 2, 3, 5, 6, 6, 6, 6, 6, 6, 6, 6, 7, 8, 9, 9, 8, 6, 4, 3], dtype=float)
    hour_w /= hour_w.sum()
    patients = []
    for i in range(60):  # a pool of anonymous historical patients
        patients.append(Patient(name=f"{np_rng.choice(NAMES)} #{i}", age=int(np_rng.integers(2, 90)),
                                medical_requirement=str(np_rng.choice(CONDITIONS)), priority="Normal"))
    db.add_all(patients)
    db.flush()
    rows_em, rows_ref = [], []
    for day in range(1, REPORT_DAYS + 1):
        for h, spec in zip(hospitals, HOSPITALS):
            size = sum(t for t, _ in spec[-1].values())
            n_em = int(np_rng.poisson(max(2, size / 40)))
            n_ref = int(np_rng.poisson(max(1, size / 60)))
            for _ in range(n_em + n_ref):
                hour = int(np_rng.choice(24, p=hour_w))
                created = (now - timedelta(days=day)).replace(hour=hour, minute=int(np_rng.integers(60)), second=0, microsecond=0)
                resp = created + timedelta(minutes=int(np_rng.integers(2, 26)))
                p = patients[int(np_rng.integers(len(patients)))]
                prio = str(np_rng.choice(["Critical", "Urgent", "Normal"], p=[0.25, 0.45, 0.30]))
                if _ < n_em:
                    rows_em.append(EmergencyRequest(
                        patient_id=p.patient_id, hospital_id=h.hospital_id, required_service=str(np_rng.choice(SERVICES)),
                        location="Karachi", condition=str(np_rng.choice(CONDITIONS)), priority=prio,
                        status=str(np_rng.choice(["Completed", "Completed", "Completed", "Declined"])),
                        source=str(np_rng.choice(["Ambulance", "Direct", "Referral"])), eta_minutes=int(np_rng.integers(4, 25)),
                        created_time=created, responded_at=resp))
                else:
                    transfer = np_rng.random() < 0.4
                    rows_ref.append(Referral(
                        patient_id=p.patient_id, to_hospital=h.hospital_id,
                        from_hospital=hospitals[int(np_rng.integers(len(hospitals)))].hospital_id if transfer else None,
                        ambulance_status="Handover complete" if transfer else None,
                        bed_type=str(np_rng.choice(["ICU", "General", "Emergency", "Ventilator"])), priority=prio,
                        status=str(np_rng.choice(["Completed", "Completed", "Accepted", "Rejected"])),
                        created_at=created, responded_at=resp, note="Historical record"))
    db.add_all(rows_em)
    db.add_all(rows_ref)
    db.flush()


def make_capacity_history(db, hospitals, np_rng, now):
    """4-hourly snapshots for HISTORY_DAYS days ending at the current real state.
    Occupancy ramps up ~1.2 points/day with weekly + daily rhythm, so the forecast has a trend to find."""
    current = hs.capacity_for(db)
    anchor = now.replace(minute=0, second=0, microsecond=0)
    anchor -= timedelta(hours=anchor.hour % 4)
    rows = []
    for h in hospitals:
        caps = current[h.hospital_id]
        for k in range(1, HISTORY_DAYS * 6 + 1):
            t = anchor - timedelta(hours=4 * (k - 1))
            days_ago = (now - t).total_seconds() / 86400
            def occ(btype, sens):
                c = caps.get(btype)
                if not c or not c["total"]:
                    return 0, 0
                now_occ = 1 - c["available"] / c["total"]
                weekly = 0.03 * np.sin(2 * np.pi * (t.weekday() - 4) / 7)
                daily = 0.05 * np.sin(2 * np.pi * (t.hour - 10) / 24)
                o = now_occ - 0.012 * sens * days_ago + weekly + daily + np_rng.normal(0, 0.015)
                return c["total"], int(round(c["total"] * min(0.99, max(0.05, o))))
            icu_t, icu_o = occ("ICU", 1.0)
            gen_t, gen_o = occ("General", 0.6)
            em_t, em_o = occ("Emergency", 1.4)
            vent_t, vent_o = occ("Ventilator", 0.8)
            ot_t, ot_o = occ("Operation Theater", 0.3)
            total = icu_t + gen_t + em_t + vent_t + ot_t
            rows.append(CapacityHistory(
                hospital_id=h.hospital_id, date=t, total_beds=total, occupied_beds=icu_o + gen_o + em_o + vent_o + ot_o,
                icu_usage=icu_o, icu_total=icu_t, general_total=gen_t, general_occupied=gen_o,
                emergency_total=em_t, emergency_occupied=em_o, emergency_requests=int(np_rng.poisson(max(3, total / 25)))))
    db.add_all(rows)
    db.flush()


def seed(reset: bool = False) -> None:
    Base.metadata.create_all(bind=engine)  # no-op when Alembic already created the schema
    rng, np_rng, now = random.Random(42), np.random.default_rng(42), utcnow()
    with SessionLocal() as db:
        if db.scalar(select(Hospital.hospital_id).limit(1)):
            if not reset:
                print("Database already has data - skipping. Use --reset to wipe and reseed.")
                return
        if reset:
            wipe(db)
        hospitals = []
        for name, area, addr, lat, lng, phone, em, spec, _ in HOSPITALS:
            h = Hospital(name=name, area=area, address=addr, latitude=lat, longitude=lng, contact_number=phone,
                         emergency_status=em, specialties=spec)
            db.add(h)
            hospitals.append(h)
        db.flush()
        make_beds(db, rng, hospitals)
        users = make_users(db, hospitals)
        make_live_requests(db, hospitals, users[0], now)   # first, so ids read EM-301.. / REF-1001..
        make_fleet(db, hospitals)
        make_request_history(db, hospitals, np_rng, now)
        make_capacity_history(db, hospitals, np_rng, now)
        db.commit()
        for h in hospitals:
            hs.record_snapshot(db, h.hospital_id, commit=True)  # snapshot of the real current state
    print(f"Seeded {len(HOSPITALS)} hospitals, demo users (password '{DEMO_PASSWORD}'):")
    for e in ("patient", "staff", "ambulance", "admin"):
        print(f"  {e}@demo.com")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--reset", action="store_true", help="delete all data first")
    seed(ap.parse_args().reset)
