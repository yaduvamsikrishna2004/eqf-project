from utils.excel_manager import create_incident, get_incidents, get_activities
from datetime import date

payload = {
    "Date": date.today(),
    "OEM": "Bosch",
    "CustomerComplaint": "Brake noise at startup",
    "DealerInfo": "Dealer A",
    "VehicleVariant": "Variant X",
    "VehicleApplication": "App Y",
    "ECUPartNumber": "ECU-1234",
    "Severity": "High",
    "IssueType": "Field Issue",
    "Custodian": "Engineer1",
    "Description": "Detailed description",
    "Status": "New",
}

incident_id = create_incident(payload)
print('CREATED', incident_id)
print('INCIDENTS COUNT', len(get_incidents()))
print('ACTIVITIES COUNT', len(get_activities()))
print(get_incidents().tail(1).to_dict(orient='records'))
print(get_activities().tail(1).to_dict(orient='records'))
