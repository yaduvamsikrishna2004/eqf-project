from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd


class AnalyticsService:
    def __init__(self, repositories) -> None:
        self.repositories = repositories

    def get_summary(self, filters: dict | None = None) -> dict:
        dataframe = self._filtered_frame(filters or {})
        return self._summary_from_frame(dataframe)

    def get_analytics(self, filters: dict | None = None) -> dict:
        dataframe = self._filtered_frame(filters or {})
        return {
            'summary': self._summary_from_frame(dataframe),
            'charts': self._charts_from_frame(dataframe),
            'insights': self._insights_from_frame(dataframe),
            'resolution_performance': self._resolution_performance(dataframe),
        }

    def list_incidents(self, filters: dict | None = None) -> list[dict]:
        dataframe = self._filtered_frame(filters or {})
        dataframe = dataframe.sort_values(by='UpdatedAt', ascending=False)
        return dataframe.fillna('').to_dict(orient='records')

    def _filtered_frame(self, filters: dict) -> pd.DataFrame:
        incidents = pd.DataFrame(self.repositories.incidents.list_all())
        if incidents.empty:
            return pd.DataFrame(columns=['IncidentID', 'OEM', 'Severity', 'Status', 'IssueType', 'CustodianName', 'CreatedAt', 'UpdatedAt'])
        resolutions = pd.DataFrame(self.repositories.resolutions.list_all())
        if resolutions.empty:
            resolutions = pd.DataFrame(columns=['IncidentID', 'TargetDate', 'ResolutionDate', 'ResolutionStatus'])
        dataframe = incidents.merge(resolutions, on='IncidentID', how='left', suffixes=('', '_resolution'))
        dataframe['CreatedAtDt'] = pd.to_datetime(dataframe['CreatedAt'], errors='coerce', utc=True)
        dataframe['UpdatedAtDt'] = pd.to_datetime(dataframe['UpdatedAt'], errors='coerce', utc=True)
        dataframe['TargetDateDt'] = pd.to_datetime(dataframe.get('TargetDate'), errors='coerce', utc=True)
        dataframe['ResolutionDateDt'] = pd.to_datetime(dataframe.get('ResolutionDate'), errors='coerce', utc=True)
        dataframe['DateDt'] = pd.to_datetime(dataframe['Date'], errors='coerce')

        search = (filters.get('search') or '').strip().lower()
        if search:
            dataframe = dataframe[
                dataframe[['IncidentID', 'OEM', 'CustomerComplaint', 'VehicleVariant', 'ECUPartNumber']]
                .fillna('')
                .apply(lambda column: column.str.lower())
                .apply(lambda column: column.str.contains(search))
                .any(axis=1)
            ]

        mapping = {
            'oem': 'OEM', 'severity': 'Severity', 'status': 'Status', 'issue_type': 'IssueType',
            'custodian': 'CustodianName', 'vehicle_variant': 'VehicleVariant',
        }
        for filter_key, column in mapping.items():
            value = filters.get(filter_key)
            if value:
                dataframe = dataframe[dataframe[column] == value]

        date_from = filters.get('date_from')
        if date_from:
            dataframe = dataframe[dataframe['DateDt'] >= pd.to_datetime(date_from)]
        date_to = filters.get('date_to')
        if date_to:
            dataframe = dataframe[dataframe['DateDt'] <= pd.to_datetime(date_to)]
        return dataframe

    def _summary_from_frame(self, dataframe: pd.DataFrame) -> dict:
        if dataframe.empty:
            return {
                'total_incidents': 0, 'open_incidents': 0, 'closed_incidents': 0, 'critical_incidents': 0,
                'overdue_incidents': 0, 'average_resolution_days': None, 'pending_validation': 0,
                'root_causes_identified': 0, 'solutions_in_progress': 0,
            }
        today = pd.Timestamp(datetime.now(timezone.utc).date(), tz='UTC')
        overdue_mask = dataframe['TargetDateDt'].notna() & (dataframe['TargetDateDt'] < today) & (dataframe['Status'] != 'Closed')
        closed = dataframe[dataframe['Status'] == 'Closed'].copy()
        avg_resolution_days = None
        if not closed.empty:
            resolution_days = (closed['ResolutionDateDt'] - closed['CreatedAtDt']).dt.total_seconds() / 86400
            if not resolution_days.dropna().empty:
                avg_resolution_days = round(float(resolution_days.dropna().mean()), 1)
        return {
            'total_incidents': int(len(dataframe)),
            'open_incidents': int((dataframe['Status'] != 'Closed').sum()),
            'closed_incidents': int((dataframe['Status'] == 'Closed').sum()),
            'critical_incidents': int((dataframe['Severity'] == 'Critical').sum()),
            'overdue_incidents': int(overdue_mask.sum()),
            'average_resolution_days': avg_resolution_days,
            'pending_validation': int((dataframe['Status'] == 'Validation').sum()),
            'root_causes_identified': int((dataframe['Status'] == 'Root Cause Identified').sum()),
            'solutions_in_progress': int((dataframe['Status'] == 'Action In Progress').sum()),
        }

    def _charts_from_frame(self, dataframe: pd.DataFrame) -> dict:
        if dataframe.empty:
            empty = {'labels': [], 'data': []}
            return {
                'oem_wise_incidents': empty,
                'severity_distribution': empty,
                'status_distribution': empty,
                'issue_type_distribution': empty,
                'monthly_incident_trend': empty,
                'custodian_workload': empty,
            }
        monthly = dataframe.assign(Month=dataframe['DateDt'].dt.strftime('%Y-%m')).groupby('Month').size().reset_index(name='Count')
        return {
            'oem_wise_incidents': self._series(dataframe.groupby('OEM').size()),
            'severity_distribution': self._series(dataframe.groupby('Severity').size()),
            'status_distribution': self._series(dataframe.groupby('Status').size()),
            'issue_type_distribution': self._series(dataframe.groupby('IssueType').size()),
            'monthly_incident_trend': {'labels': monthly['Month'].tolist(), 'data': monthly['Count'].astype(int).tolist()},
            'custodian_workload': self._series(dataframe.groupby('CustodianName').size()),
        }

    def _insights_from_frame(self, dataframe: pd.DataFrame) -> list[str]:
        if dataframe.empty:
            return ['No incidents found for the selected filters.']
        issue_share = dataframe['IssueType'].value_counts(normalize=True).mul(100).round(0)
        top_oem = dataframe['OEM'].value_counts().idxmax()
        critical_open = len(dataframe[(dataframe['Severity'] == 'Critical') & (dataframe['Status'] != 'Closed')])
        top_custodian = dataframe[dataframe['Status'] != 'Closed']['CustodianName'].value_counts()
        top_custodian_name = top_custodian.idxmax() if not top_custodian.empty else 'No active custodian'
        insights = [
            f"Field issues represent {int(issue_share.get('Field Issue', 0))}% of total incidents.",
            f"{top_oem} has the highest number of incidents.",
            f"There are {critical_open} critical incidents currently open.",
            f"{top_custodian_name} has the highest active workload.",
        ]
        average_days = self._summary_from_frame(dataframe)['average_resolution_days']
        insights.append(f"Average resolution time is {average_days} days." if average_days is not None else 'Average resolution time is N/A.')
        return insights

    def _resolution_performance(self, dataframe: pd.DataFrame) -> list[dict]:
        if dataframe.empty:
            return []
        result = []
        for custodian, group in dataframe.groupby('CustodianName'):
            closed = group[group['Status'] == 'Closed']
            avg_days = None
            if not closed.empty:
                values = (closed['ResolutionDateDt'] - closed['CreatedAtDt']).dt.total_seconds() / 86400
                if not values.dropna().empty:
                    avg_days = round(float(values.dropna().mean()), 1)
            result.append({
                'custodian': custodian,
                'total': int(len(group)),
                'open': int((group['Status'] != 'Closed').sum()),
                'closed': int((group['Status'] == 'Closed').sum()),
                'critical': int((group['Severity'] == 'Critical').sum()),
                'average_resolution_days': avg_days,
            })
        return result

    @staticmethod
    def _series(series: pd.Series) -> dict:
        return {'labels': list(series.index), 'data': [int(value) for value in series.tolist()]}
