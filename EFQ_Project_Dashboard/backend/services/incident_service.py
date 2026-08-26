from __future__ import annotations

from datetime import date

from fastapi import HTTPException, status

from models.incident import IncidentCreateRequest, IncidentResponse, IncidentUpdateRequest
from utils.security import now_iso


class IncidentService:
    def __init__(self, repositories) -> None:
        self.repositories = repositories

    def list_custodians(self) -> list[dict]:
        return [
            {'ntid': row['NTID'], 'full_name': row['FullName']}
            for row in self.repositories.users.list_custodians()
        ]

    def create_incident(self, payload: IncidentCreateRequest, current_user) -> IncidentResponse:
        custodian = self.repositories.users.get_by_ntid(payload.custodian_ntid)
        if not custodian or custodian['Role'] != 'Custodian' or custodian['AccountStatus'] != 'Active':
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Selected custodian is not available.')

        incident_id = self._next_incident_id(payload.date)
        timestamp = now_iso()
        status_value = 'Draft' if payload.draft else 'New'
        title = payload.incident_title.strip() if payload.incident_title else payload.customer_complaint[:80]
        row = {
            'IncidentID': incident_id,
            'IncidentTitle': title,
            'Date': payload.date.isoformat(),
            'OEM': payload.oem,
            'CustomerComplaint': payload.customer_complaint,
            'DealerName': payload.dealer_name,
            'DealerLocation': payload.dealer_location,
            'DealerContact': payload.dealer_contact,
            'VehicleModel': payload.vehicle_model,
            'VehicleVariant': payload.vehicle_variant,
            'VehicleApplication': payload.vehicle_application,
            'VIN': payload.vin,
            'KilometerReading': payload.kilometer_reading,
            'ECUPartNumber': payload.ecu_part_number,
            'ECUName': payload.ecu_name,
            'Severity': payload.severity,
            'IssueType': payload.issue_type,
            'CustodianNTID': custodian['NTID'],
            'CustodianName': custodian['FullName'],
            'Description': payload.description,
            'Status': status_value,
            'CreatedBy': current_user.ntid,
            'CreatedAt': timestamp,
            'UpdatedBy': current_user.ntid,
            'UpdatedAt': timestamp,
        }
        self.repositories.incidents.create(row)
        self._log_activity(incident_id, 'Incident Created', current_user.ntid, current_user.full_name)
        return self._serialize_incident(row)

    def get_incident(self, incident_id: str) -> IncidentResponse:
        row = self.repositories.incidents.get_by_id(incident_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Incident not found.')
        return self._serialize_incident(row)

    def update_incident(self, incident_id: str, payload: IncidentUpdateRequest, current_user) -> IncidentResponse:
        existing = self.repositories.incidents.get_by_id(incident_id)
        if not existing:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Incident not found.')
        if existing['Status'] != 'Draft' and current_user.role not in ('Admin', 'Manager'):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Only drafts can be edited after creation.')

        updates = {key: value for key, value in payload.model_dump(exclude_none=True).items()}
        translated = {
            'date': 'Date', 'oem': 'OEM', 'dealer_name': 'DealerName', 'dealer_location': 'DealerLocation',
            'dealer_contact': 'DealerContact', 'vehicle_model': 'VehicleModel', 'vehicle_variant': 'VehicleVariant',
            'vehicle_application': 'VehicleApplication', 'vin': 'VIN', 'kilometer_reading': 'KilometerReading',
            'ecu_part_number': 'ECUPartNumber', 'ecu_name': 'ECUName', 'severity': 'Severity',
            'issue_type': 'IssueType', 'custodian_ntid': 'CustodianNTID', 'description': 'Description',
            'customer_complaint': 'CustomerComplaint',
        }
        normalized_updates = {}
        if 'custodian_ntid' in updates:
            custodian = self.repositories.users.get_by_ntid(updates['custodian_ntid'])
            if not custodian or custodian['Role'] != 'Custodian':
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Selected custodian is not available.')
            normalized_updates['CustodianNTID'] = custodian['NTID']
            normalized_updates['CustodianName'] = custodian['FullName']
        for key, value in updates.items():
            if key == 'custodian_ntid':
                continue
            normalized_updates[translated[key]] = value.isoformat() if hasattr(value, 'isoformat') else value
        normalized_updates['UpdatedAt'] = now_iso()
        normalized_updates['UpdatedBy'] = current_user.ntid
        updated = self.repositories.incidents.update(incident_id, normalized_updates)
        self._log_activity(incident_id, 'Incident Updated', current_user.ntid, current_user.full_name)
        return self._serialize_incident(updated)

    def submit_incident(self, incident_id: str, current_user) -> IncidentResponse:
        existing = self.repositories.incidents.get_by_id(incident_id)
        if not existing:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Incident not found.')
        updated = self.repositories.incidents.update(
            incident_id,
            {'Status': 'New', 'UpdatedAt': now_iso(), 'UpdatedBy': current_user.ntid},
        )
        self._log_activity(incident_id, 'Status Changed', current_user.ntid, current_user.full_name)
        return self._serialize_incident(updated)

    def _next_incident_id(self, incident_date: date) -> str:
        prefix = incident_date.strftime('EFQ-%Y%m%d-')
        existing_ids = [row['IncidentID'] for row in self.repositories.incidents.list_all() if str(row['IncidentID']).startswith(prefix)]
        next_index = 1
        if existing_ids:
            next_index = max(int(value.split('-')[-1]) for value in existing_ids) + 1
        return f'{prefix}{next_index:04d}'

    def _log_activity(self, incident_id: str, action: str, user_ntid: str, user_name: str) -> None:
        activity_id = f"ACT-{len(self.repositories.activities.list_all()) + 1:06d}"
        self.repositories.activities.add({
            'ActivityID': activity_id,
            'IncidentID': incident_id,
            'Action': action,
            'UserNTID': user_ntid,
            'UserName': user_name,
            'Timestamp': now_iso(),
        })

    @staticmethod
    def _serialize_incident(row: dict) -> IncidentResponse:
        return IncidentResponse(
            incident_id=row['IncidentID'],
            incident_title=row['IncidentTitle'],
            date=row['Date'],
            oem=row['OEM'],
            customer_complaint=row['CustomerComplaint'],
            dealer_name=row['DealerName'],
            dealer_location=row['DealerLocation'],
            dealer_contact=row['DealerContact'],
            vehicle_model=row['VehicleModel'],
            vehicle_variant=row['VehicleVariant'],
            vehicle_application=row['VehicleApplication'],
            vin=row['VIN'],
            kilometer_reading=int(row['KilometerReading'] or 0),
            ecu_part_number=row['ECUPartNumber'],
            ecu_name=row['ECUName'],
            severity=row['Severity'],
            issue_type=row['IssueType'],
            custodian_ntid=row['CustodianNTID'],
            custodian_name=row['CustodianName'],
            description=row['Description'],
            status=row['Status'],
            created_by=row['CreatedBy'],
            created_at=row['CreatedAt'],
            updated_by=row['UpdatedBy'],
            updated_at=row['UpdatedAt'],
        )
