"""End-to-end tests following the demo flow from the project brief."""
from tests.conftest import login


# ------------------------------------------------------------------ auth & RBAC
def test_register_login_and_role_checks(client):
    r = client.post("/api/auth/register", json={"name": "New Pat", "email": "new@demo.com", "password": "secret1", "role": "patient"})
    assert r.status_code == 201 and r.json()["role"] == "patient"
    assert client.post("/api/auth/register", json={"name": "x", "email": "NEW@demo.com", "password": "secret1"}).status_code == 409
    ok = client.post("/api/auth/login", json={"email": "new@demo.com", "password": "secret1", "role": "patient"})
    assert ok.status_code == 200 and ok.json()["token"] and ok.json()["user"]["role"] == "patient"
    assert client.post("/api/auth/login", json={"email": "new@demo.com", "password": "wrong"}).status_code == 401
    # wrong role picked on the login page
    assert client.post("/api/auth/login", json={"email": "new@demo.com", "password": "secret1", "role": "admin"}).status_code == 403
    # role aliases from the spec are accepted
    r = client.post("/api/auth/register", json={"name": "Amb", "email": "amb2@demo.com", "password": "secret1", "role": "Ambulance Coordinator"})
    assert r.json()["role"] == "ambulance"


def test_auth_required_and_forbidden(client, patient, staff):
    assert client.get("/api/hospitals").status_code == 401
    assert client.get("/api/reports", headers=patient).status_code == 403
    assert client.post("/api/hospitals", headers=staff, json={"name": "X Hosp", "latitude": 1, "longitude": 1}).status_code == 403
    assert client.get("/api/emergency-requests", headers=patient).status_code == 403


# ------------------------------------------------------------------ hospitals (frontend shape)
def test_hospital_shape_matches_frontend(client, patient):
    hs = client.get("/api/hospitals", headers=patient).json()
    assert len(hs) == 6
    h = hs[0]
    for key in ("id", "name", "area", "distanceKm", "phone", "x", "y", "specialties", "status", "beds"):
        assert key in h
    for t in ("ICU", "General", "Emergency", "Ventilator"):
        assert set(h["beds"][t]) == {"total", "available"}
    assert h["beds"]["ICU"] == {"total": 30, "available": 6}
    by_name = {x["name"]: x for x in hs}
    assert by_name["Lakeshore Trauma Institute"]["status"] == "critical"
    assert by_name["Riverside General Hospital"]["status"] == "normal"
    assert client.get("/api/hospitals/1", headers=patient).json()["name"] == "Riverside General Hospital"
    assert client.get("/api/hospitals/999", headers=patient).status_code == 404


# ------------------------------------------------------------------ the demo flow
def test_patient_request_to_ambulance_flow(client, patient, staff, amb):
    icu_before = client.get("/api/hospitals/1", headers=staff).json()["beds"]["ICU"]["available"]

    # patient asks the AI for the best ICU hospital
    rec = client.post("/api/ai/recommend", headers=patient, json={"bedType": "ICU", "priority": "Critical"}).json()
    assert rec["recommended"]["available"] > 0 and "reason" in rec["recommended"]
    assert rec["recommended"]["scoreBreakdown"].keys() == {"availability", "distance", "capability", "waiting"}
    hid = rec["recommended"]["hospitalId"]

    # patient sends the request (same payload as the BedRequest page)
    r = client.post("/api/bed-requests", headers=patient, json={
        "hospitalId": hid, "bedType": "ICU", "priority": "Critical", "patientName": "Demo Patient", "condition": "Chest pain"})
    assert r.status_code == 201, r.text
    ref = r.json()
    assert ref["id"].startswith("REF-") and ref["status"] == "Pending"

    # it shows up in the patient's tracker
    mine = client.get("/api/referrals", headers=patient).json()
    assert any(x["id"] == ref["id"] for x in mine)
    assert any(x["id"] == ref["id"] for x in client.get("/api/patient/status", headers=patient).json())

    # hospital staff (of the chosen hospital) accepts -> a bed becomes Reserved -> availability drops
    from tests.conftest import login as _login
    owner = staff if hid == 1 else _login(client, "admin@demo.com", "admin")
    before = client.get(f"/api/hospitals/{hid}", headers=owner).json()["beds"]["ICU"]["available"]
    r = client.put(f"/api/referral/{ref['id']}/status", headers=owner, json={"status": "Accepted"})
    assert r.status_code == 200, r.text
    after = client.get(f"/api/hospitals/{hid}", headers=owner).json()["beds"]["ICU"]["available"]
    assert after == before - 1

    # ambulance transfer, steps must be in order
    s = lambda step: client.put(f"/api/referral/{ref['id']}/status", headers=amb, json={"ambulanceStatus": step})
    assert s("Arrived at hospital").status_code == 409
    t = client.post("/api/referral/create", headers=amb, json={"referralId": ref["id"], "pickupLocation": "Saddar", "ambulanceId": "A-15"})
    assert t.status_code == 201 and t.json()["ambulanceStatus"] == "Patient picked up"
    assert s("En route to hospital").status_code == 200
    assert s("Arrived at hospital").status_code == 200
    done = s("Handover complete").json()
    assert done["status"] == "Completed"
    fleet = {a["id"]: a for a in client.get("/api/ambulances", headers=amb).json()}
    assert fleet["A-15"]["status"] == "Available"
    assert icu_before >= 0


def test_no_bed_means_409_and_rejection_releases(client, patient, staff):
    # Lakeshore (id 3) has 0 ICU beds
    r = client.post("/api/bed-requests", headers=patient, json={
        "hospitalId": 3, "bedType": "ICU", "patientName": "P", "condition": "x"})
    assert r.status_code == 409 and "no free ICU" in r.json()["detail"]
    # priority aliases from the frontend ("High") are accepted
    r = client.post("/api/bed-requests", headers=patient, json={
        "hospitalId": 1, "bedType": "General", "priority": "High", "patientName": "P", "condition": "x"})
    assert r.status_code == 201 and r.json()["priority"] == "Urgent"
    rid = r.json()["id"]
    gen = lambda: client.get("/api/hospitals/1", headers=staff).json()["beds"]["General"]["available"]
    g0 = gen()
    assert client.put(f"/api/referral/{rid}/status", headers=staff, json={"status": "Accepted"}).status_code == 200
    assert gen() == g0 - 1
    assert client.put(f"/api/referral/{rid}/status", headers=staff, json={"status": "Cancelled"}).status_code == 200
    assert gen() == g0  # released
    assert client.put(f"/api/referral/{rid}/status", headers=staff, json={"status": "Accepted"}).status_code == 409


def test_ai_picks_hospital_when_none_given(client, patient):
    r = client.post("/api/patient/request-bed", headers=patient, json={"bedType": "Ventilator", "priority": "Critical", "patientName": "Z", "condition": "y"})
    assert r.status_code == 201
    assert r.json()["recommendation"]["hospitalId"] == r.json()["hospitalId"]


# ------------------------------------------------------------------ capacity (hospital staff)
def test_update_capacity_and_dashboard(client, staff, patient, admin):
    body = {"beds": {"ICU": {"total": 30, "available": 10}, "General": {"total": 180, "available": 52},
                     "Emergency": {"total": 40, "available": 11}, "Ventilator": {"total": 24, "available": 9}}}
    r = client.put("/api/hospitals/1/capacity", headers=staff, json=body)
    assert r.status_code == 200, r.text
    icu = r.json()["beds"]["ICU"]
    assert icu["available"] == 10 and icu["total"] == 30
    # staff of hospital 1 cannot touch hospital 2; patients cannot touch anything
    assert client.put("/api/hospitals/2/capacity", headers=staff, json=body).status_code == 403
    assert client.put("/api/hospitals/1/capacity", headers=patient, json=body).status_code == 403
    bad = {"beds": {"ICU": {"total": 5, "available": 9}}}
    assert client.put("/api/hospitals/1/capacity", headers=staff, json=bad).status_code == 422
    # dashboard reflects the change immediately
    d = client.get("/api/analytics/dashboard", headers=staff).json()
    assert d["totalHospitals"] == 1 and d["icuAvailable"] == 10
    net = client.get("/api/analytics/dashboard", headers=admin).json()
    assert net["totalHospitals"] == 6 and net["emergencyRequests"] >= 4


def test_bed_status_admit_discharge(client, staff):
    beds = client.get("/api/beds", headers=staff).json()
    assert beds[0].keys() >= {"id", "ward", "status", "patient"}
    free = next(b for b in beds if b["ward"] == "General" and b["status"] == "Available")
    gen = lambda: client.get("/api/hospitals/1", headers=staff).json()["beds"]["General"]["available"]
    g0 = gen()
    r = client.put(f"/api/beds/{free['id']}", headers=staff, json={"status": "Occupied", "patient": "J. Doe"})  # by code
    assert r.status_code == 200 and r.json()["patient"] == "J. Doe"
    assert gen() == g0 - 1
    r = client.put(f"/api/beds/{free['bedId']}", headers=staff, json={"status": "Available"})  # discharge, by numeric id
    assert r.status_code == 200 and r.json()["patient"] == ""
    assert gen() == g0
    assert client.put("/api/beds/ICU-9999", headers=staff, json={"status": "Available"}).status_code == 404
    assert client.put(f"/api/beds/{free['id']}", headers=staff, json={"status": "Nope"}).status_code == 422
    new = client.post("/api/beds", headers=staff, json={"bedType": "ICU Bed"})
    assert new.status_code == 201 and new.json()["ward"] == "ICU"
    assert client.get("/api/beds/available?bed_type=ICU", headers=staff).json()[0]["byType"]["ICU"] >= 1


# ------------------------------------------------------------------ emergencies: critical first
def test_emergency_priority_and_decisions(client, staff, patient):
    rows = client.get("/api/emergency-requests", headers=staff).json()
    prios = [r["priority"] for r in rows]
    assert prios.index("Critical") == 0 and prios == sorted(prios, key=["Critical", "Urgent", "Normal"].index)
    assert rows[0].keys() >= {"id", "patient", "condition", "priority", "bedType", "eta", "source"}
    assert rows[0]["id"].startswith("EM-30")

    new = client.post("/api/emergency/request", headers=patient, json={
        "condition": "Collapsed, not breathing", "bedType": "ICU", "priority": "Critical", "latitude": 24.86, "longitude": 67.0})
    assert new.status_code == 201, new.text
    assert new.json()["hospitalId"] and new.json()["recommendation"]["reason"]
    first = client.get("/api/emergency-requests", headers=staff).json()[0]
    assert first["priority"] == "Critical"

    eid = rows[0]["id"]
    assert client.put(f"/api/emergency/{eid}/status", headers=staff, json={"status": "Accepted"}).status_code == 200
    assert client.put(f"/api/emergency/{eid}/status", headers=staff, json={"status": "Pending"}).status_code == 409
    assert client.put(f"/api/emergency/{eid}/status", headers=staff, json={"status": "Admitted"}).json()["status"] == "Admitted"

    near = client.get("/api/emergency/nearby-hospitals?bed_type=ICU&lat=24.86&lng=67.0", headers=patient).json()
    assert near and near[0]["available"] > 0 and near[0]["score"] >= near[-1]["score"]


def test_critical_patients_go_first(client, patient, staff):
    """Hospital 3 has 0 ICU, so use hospital 4's Ventilator beds: fill the queue with a critical request,
    then a Normal request may not take the last bed."""
    hid = 4
    admin = login(client, "admin@demo.com", "admin")
    caps = client.get(f"/api/hospitals/{hid}", headers=admin).json()["beds"]["Ventilator"]
    # leave exactly 1 free ventilator
    client.put(f"/api/hospitals/{hid}/capacity", headers=login(client, "admin@demo.com", "admin"),
               json={"beds": {"Ventilator": {"total": caps["total"], "available": 1}}})
    normal = client.post("/api/bed-requests", headers=patient, json={
        "hospitalId": hid, "bedType": "Ventilator", "priority": "Normal", "patientName": "N", "condition": "c"}).json()
    crit = client.post("/api/bed-requests", headers=patient, json={
        "hospitalId": hid, "bedType": "Ventilator", "priority": "Critical", "patientName": "C", "condition": "c"}).json()
    r = client.put(f"/api/referral/{normal['id']}/status", headers=admin, json={"status": "Accepted"})
    assert r.status_code == 409 and "critical" in r.json()["detail"].lower()
    assert client.put(f"/api/referral/{crit['id']}/status", headers=admin, json={"status": "Accepted"}).status_code == 200


# ------------------------------------------------------------------ AI & analytics
def test_ai_chat_predict_alerts(client, patient, admin, staff):
    c = client.post("/api/ai/chat", headers=patient, json={"message": "Need emergency ICU"}).json()
    assert c["intent"] == "availability" and "ICU" in c["reply"] and "available at" in c["reply"]
    assert client.post("/api/assistant", headers=patient, json={"message": "nearest hospital?"}).json()["reply"].startswith("The closest")
    p = client.get("/api/ai/predict?bed_type=ICU", headers=patient).json()
    assert p["daysOfHistory"] >= 10 and "demand" in p["message"] and len(p["forecast"]) == 3
    assert client.get("/api/ai/predict?hospital_id=1", headers=patient).status_code == 200
    f = client.post("/api/ai/chat", headers=patient, json={"message": "forecast icu tomorrow"}).json()
    assert f["intent"] == "forecast"
    al = client.get("/api/analytics/alerts", headers=admin).json()
    assert any(a["type"] == "icu_overload" and a["hospital"].startswith("Lakeshore") for a in al)


def test_chart_and_report_endpoints(client, admin, staff):
    occ = client.get("/api/analytics/occupancy", headers=admin).json()
    assert occ and set(occ[0]) == {"time", "ICU", "General", "Emergency"}
    cap = client.get("/api/analytics/capacity", headers=admin).json()
    assert len(cap["byHospital"]) == 6 and cap["daily"]
    rep = client.get("/api/reports", headers=admin).json()
    assert rep and set(rep[0]) == {"period", "admissions", "transfers", "avgWait", "peak"}
    amb = client.get("/api/ambulances", headers=staff).json()
    assert {"id", "crew", "status", "destination", "eta"} == set(amb[0])


def test_admin_registers_hospital(client, admin, patient):
    r = client.post("/api/hospitals", headers=admin, json={
        "name": "New Valley Hospital", "latitude": 24.9, "longitude": 67.1, "phone": "+92 21 555 0199",
        "beds": {"ICU": 5, "General Bed": 20}})
    assert r.status_code == 201, r.text
    assert r.json()["beds"]["ICU"] == {"total": 5, "available": 5}
    assert client.post("/api/hospitals", headers=admin, json={"name": "new valley hospital", "latitude": 1, "longitude": 1}).status_code == 409
    assert len(client.get("/api/hospitals", headers=patient).json()) == 7
