from __future__ import annotations

from fastapi import HTTPException, status

from models.resolution import ResolutionResponse, ResolutionUpdateRequest
from utils.security import now_iso


STATUS_MAP = {
    'Not Started': 'New',
    'Investigation': 'Investigation Started',
    'Root Cause Identified': 'Root Cause Identified',
    'Action In Progress': 'Action In Progress',
    'Validation': 'Validation',
    'Closed': 'Closed',
}


class ResolutionService:
    def __init__(self, repositories) -> None:
        self.repositories = repositories

    def list_incidents_for_custodian(self, current_user) -> list[dict]:
        incidents = self.repositories.incidents.list_all()
        if current_user.role == 'Admin':
            visible = incidents
        else:
            visible = [row for row in incidents if row['CustodianNTID'] == current_user.ntid]
        visible.sort(key=lambda row: row['UpdatedAt'], reverse=True)
        return [self._compose_incident_summary(row) for row in visible]

    def get_incident_detail(self, incident_id: str, current_user) -> dict:
        incident = self.repositories.incidents.get_by_id(incident_id)
        if not incident:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Incident not found.')
        self._authorize_incident_access(incident, current_user)
        resolution = self.repositories.resolutions.get_by_incident_id(incident_id)
        activities = self.repositories.activities.list_by_incident_id(incident_id)
        activities.sort(key=lambda row: row['Timestamp'], reverse=True)
        return {
            'incident': self._compose_incident_summary(incident, include_full=True),
            'resolution': self._serialize_resolution(resolution) if resolution else None,
            'activities': [self._serialize_activity(row) for row in activities],
        }

    def update_resolution(self, incident_id: str, payload: ResolutionUpdateRequest, current_user) -> dict:
        incident = self.repositories.incidents.get_by_id(incident_id)
        if not incident:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Incident not found.')
        self._authorize_incident_access(incident, current_user, write=True)

        existing = self.repositories.resolutions.get_by_incident_id(incident_id) or {}
        timestamp = now_iso()
        resolution_date = existing.get('ResolutionDate', '')
        if payload.resolution_status == 'Closed':
            required = [payload.root_cause, payload.recommendation, payload.proposed_solution, payload.corrective_action, payload.validation_method]
            if not all(value.strip() for value in required) or payload.validation_result != 'Pass':
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Closing an incident requires root cause, recommendation, solution, corrective action, validation method, and validation result Pass.')
            resolution_date = timestamp

        resolution_row = {
            'ResolutionID': existing.get('ResolutionID') or f"RES-{len(self.repositories.resolutions.list_all()) + 1:06d}",
            'IncidentID': incident_id,
            'InvestigationDetails': payload.investigation_details,
            'RootCause': payload.root_cause,
            'Recommendation': payload.recommendation,
            'ProposedSolution': payload.proposed_solution,
            'CorrectiveAction': payload.corrective_action,
            'PreventiveAction': payload.preventive_action,
            'ValidationMethod': payload.validation_method,
            'ValidationResult': payload.validation_result,
            'ValidationDate': payload.validation_date.isoformat() if payload.validation_date else '',
            'ResolutionOwner': current_user.ntid,
            'TargetDate': payload.target_date.isoformat() if payload.target_date else '',
            'ResolutionDate': resolution_date,
            'ResolutionStatus': payload.resolution_status,
            'Remarks': payload.remarks,
            'CreatedAt': existing.get('CreatedAt') or timestamp,
            'UpdatedAt': timestamp,
        }
        self.repositories.resolutions.upsert(incident_id, resolution_row)

        incident_updates = {
            'Status': STATUS_MAP[payload.resolution_status],
            'UpdatedAt': timestamp,
            'UpdatedBy': current_user.ntid,
        }
        self.repositories.incidents.update(incident_id, incident_updates)
        self._log_field_activities(existing, resolution_row, current_user, incident_id)
        if payload.resolution_status == 'Closed':
            self._log_activity(incident_id, 'Incident Closed', current_user.ntid, current_user.full_name)
        elif existing.get('ResolutionStatus') != payload.resolution_status:
            self._log_activity(incident_id, 'Status Changed', current_user.ntid, current_user.full_name)

        return self.get_incident_detail(incident_id, current_user)

    def list_activities(self, incident_id: str, current_user) -> list[dict]:
        incident = self.repositories.incidents.get_by_id(incident_id)
        if not incident:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Incident not found.')
        self._authorize_incident_access(incident, current_user)
        return [self._serialize_activity(row) for row in self.repositories.activities.list_by_incident_id(incident_id)]

    def _authorize_incident_access(self, incident: dict, current_user, write: bool = False) -> None:
        if current_user.role == 'Admin':
            return
        if current_user.role != 'Custodian':
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Custodian access only.')
        if incident['CustodianNTID'] != current_user.ntid:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='You are not assigned to this incident.')

    def _log_field_activities(self, existing: dict, current: dict, current_user, incident_id: str) -> None:
        action_map = {
            'InvestigationDetails': 'Investigation Updated',
            'RootCause': 'Root Cause Added',
            'Recommendation': 'Recommendation Added',
            'ProposedSolution': 'Solution Added',
            'CorrectiveAction': 'Corrective Action Added',
            'PreventiveAction': 'Preventive Action Added',
            'ValidationMethod': 'Validation Updated',
            'ValidationResult': 'Validation Updated',
        }
        logged_actions = set()
        for field, action in action_map.items():
            before = (existing.get(field) or '').strip()
            after = (current.get(field) or '').strip()
            if before != after and after and action not in logged_actions:
                self._log_activity(incident_id, action, current_user.ntid, current_user.full_name)
                logged_actions.add(action)

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

    def _compose_incident_summary(self, incident: dict, include_full: bool = False) -> dict:
        resolution = self.repositories.resolutions.get_by_incident_id(incident['IncidentID']) or {}
        summary = {
            'incident_id': incident['IncidentID'],
            'incident_title': incident['IncidentTitle'],
            'oem': incident['OEM'],
            'severity': incident['Severity'],
            'issue_type': incident['IssueType'],
            'customer_complaint': incident['CustomerComplaint'],
            'status': incident['Status'],
            'target_date': resolution.get('TargetDate') or '',
            'updated_at': incident['UpdatedAt'],
            'custodian_ntid': incident['CustodianNTID'],
            'custodian_name': incident['CustodianName'],
            'vehicle_variant': incident['VehicleVariant'],
            'ecu_part_number': incident['ECUPartNumber'],
            'created_at': incident['CreatedAt'],
        }
        if include_full:
            summary.update({
                'date': incident['Date'], 'dealer_name': incident['DealerName'], 'dealer_location': incident['DealerLocation'],
                'dealer_contact': incident['DealerContact'], 'vehicle_model': incident['VehicleModel'], 'vehicle_application': incident['VehicleApplication'],
                'vin': incident['VIN'], 'kilometer_reading': int(incident['KilometerReading'] or 0), 'ecu_name': incident['ECUName'],
                'description': incident['Description'],
            })
        return summary

    @staticmethod
    def _serialize_resolution(row: dict) -> ResolutionResponse:
        return ResolutionResponse(
            resolution_id=row['ResolutionID'], incident_id=row['IncidentID'], investigation_details=row['InvestigationDetails'],
            root_cause=row['RootCause'], recommendation=row['Recommendation'], proposed_solution=row['ProposedSolution'],
            corrective_action=row['CorrectiveAction'], preventive_action=row['PreventiveAction'], validation_method=row['ValidationMethod'],
            validation_result=row['ValidationResult'], validation_date=row.get('ValidationDate') or None, resolution_owner=row['ResolutionOwner'],
            target_date=row.get('TargetDate') or None, resolution_date=row.get('ResolutionDate') or None, resolution_status=row['ResolutionStatus'],
            remarks=row['Remarks'], created_at=row['CreatedAt'], updated_at=row['UpdatedAt'],
        )

    @staticmethod
    def _serialize_activity(row: dict) -> dict:
        return {
            'activity_id': row['ActivityID'],
            'incident_id': row['IncidentID'],
            'action': row['Action'],
            'user_ntid': row['UserNTID'],
            'user_name': row['UserName'],
            'timestamp': row['Timestamp'],
        }
