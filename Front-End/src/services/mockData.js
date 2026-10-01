// Demo data used whenever the backend is unreachable.
const bed = (total, available) => ({ total, available });

export const hospitals = [
  { id: 1, name: 'Riverside General Hospital', area: 'Central District', distanceKm: 2.4, phone: '+1 555 0101', x: 38, y: 42, specialties: ['Cardiology', 'Trauma', 'Neurology'], status: 'normal',
    beds: { ICU: bed(30, 6), General: bed(180, 52), Emergency: bed(40, 11), Ventilator: bed(24, 9) } },
  { id: 2, name: 'St. Mary Medical Center', area: 'North Park', distanceKm: 4.1, phone: '+1 555 0102', x: 62, y: 24, specialties: ['Pediatrics', 'Maternity'], status: 'busy',
    beds: { ICU: bed(20, 2), General: bed(120, 18), Emergency: bed(25, 3), Ventilator: bed(12, 2) } },
  { id: 3, name: 'Lakeshore Trauma Institute', area: 'Lakeshore', distanceKm: 6.8, phone: '+1 555 0103', x: 78, y: 62, specialties: ['Trauma', 'Burns', 'Orthopedics'], status: 'critical',
    beds: { ICU: bed(25, 0), General: bed(90, 4), Emergency: bed(30, 1), Ventilator: bed(15, 0) } },
  { id: 4, name: 'Hillcrest Community Hospital', area: 'West Hills', distanceKm: 3.3, phone: '+1 555 0104', x: 20, y: 66, specialties: ['General Medicine', 'Oncology'], status: 'normal',
    beds: { ICU: bed(15, 7), General: bed(140, 64), Emergency: bed(20, 9), Ventilator: bed(10, 6) } },
];

export const patientRequests = [
  { id: 'REF-1042', hospital: 'Riverside General Hospital', bedType: 'ICU', status: 'Accepted', time: '10 min ago', note: 'Bed reserved. Arrive within 30 minutes.' },
  { id: 'REF-1037', hospital: 'St. Mary Medical Center', bedType: 'General', status: 'Pending', time: '35 min ago', note: 'Waiting for hospital response.' },
  { id: 'REF-1029', hospital: 'Lakeshore Trauma Institute', bedType: 'Emergency', status: 'Rejected', time: '2 h ago', note: 'No emergency beds available. Try another hospital.' },
];

export const emergencyRequests = [
  { id: 'EM-301', patient: 'Male, 54', condition: 'Suspected cardiac arrest', priority: 'Critical', bedType: 'ICU', eta: '6 min', source: 'Ambulance A-12' },
  { id: 'EM-302', patient: 'Female, 29', condition: 'Road accident, fractures', priority: 'High', bedType: 'Emergency', eta: '12 min', source: 'Ambulance A-07' },
  { id: 'EM-303', patient: 'Child, 7', condition: 'Severe asthma attack', priority: 'High', bedType: 'Emergency', eta: '9 min', source: 'Referral' },
  { id: 'EM-304', patient: 'Male, 71', condition: 'Stroke symptoms', priority: 'Critical', bedType: 'ICU', eta: '15 min', source: 'Ambulance A-03' },
];

export const wards = [
  { id: 'ICU-01', ward: 'ICU', status: 'Occupied', patient: 'A. Khan' },
  { id: 'ICU-02', ward: 'ICU', status: 'Available', patient: '' },
  { id: 'ICU-03', ward: 'ICU', status: 'Cleaning', patient: '' },
  { id: 'GEN-11', ward: 'General', status: 'Occupied', patient: 'R. Silva' },
  { id: 'GEN-12', ward: 'General', status: 'Available', patient: '' },
  { id: 'EMR-04', ward: 'Emergency', status: 'Reserved', patient: 'EM-301' },
  { id: 'VEN-02', ward: 'Ventilator', status: 'Available', patient: '' },
  { id: 'VEN-03', ward: 'Ventilator', status: 'Occupied', patient: 'M. Osei' },
];

export const occupancyTrend = ['00', '04', '08', '12', '16', '20'].map((h, i) => ({
  time: `${h}:00`, ICU: [58, 61, 70, 76, 82, 74][i], General: [52, 50, 60, 68, 71, 63][i], Emergency: [40, 36, 55, 72, 85, 78][i],
}));

export const ambulances = [
  { id: 'A-12', crew: 'Crew Delta', status: 'En route', destination: 'Riverside General Hospital', eta: '6 min' },
  { id: 'A-07', crew: 'Crew Echo', status: 'On scene', destination: 'Unassigned', eta: '-' },
  { id: 'A-03', crew: 'Crew Alpha', status: 'En route', destination: 'Hillcrest Community Hospital', eta: '15 min' },
  { id: 'A-15', crew: 'Crew Bravo', status: 'Available', destination: '-', eta: '-' },
];

export const reportRows = [
  { period: 'Week 36', admissions: 1240, transfers: 188, avgWait: '14 min', peak: 'Fri 18:00' },
  { period: 'Week 37', admissions: 1312, transfers: 203, avgWait: '16 min', peak: 'Sat 20:00' },
  { period: 'Week 38', admissions: 1275, transfers: 177, avgWait: '12 min', peak: 'Fri 17:00' },
  { period: 'Week 39', admissions: 1390, transfers: 221, avgWait: '18 min', peak: 'Sat 19:00' },
];
