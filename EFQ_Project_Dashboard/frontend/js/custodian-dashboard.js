document.addEventListener('DOMContentLoaded', async () => {
  const user = await window.EFQNavigation.bootProtectedPage(
    'custodian-dashboard',
    'Custodian Dashboard',
    'Review assigned incidents, capture investigation detail, and close validated actions.'
  );
  if (!user) return;

  const tableBody = document.getElementById('custodianIncidentRows');
  const metrics = document.getElementById('custodianMetrics');
  const detailPanel = document.getElementById('custodianDetailPanel');
  const emptyPanel = document.getElementById('custodianEmptyState');
  const filtersForm = document.getElementById('custodianFilters');
  let incidents = [];
  let currentIncidentId = null;

  async function loadIncidents() {
    try {
      incidents = await window.EFQApi.get('/api/custodian/incidents');
      renderMetrics();
      renderTable();
      if (!incidents.length) {
        emptyPanel.hidden = false;
        detailPanel.hidden = true;
      } else if (!currentIncidentId) {
        await loadDetail(incidents[0].incident_id);
      }
    } catch (error) {
      window.EFQUI.showToast(error.message, 'error');
    }
  }

  function applyFilters() {
    const formValues = Object.fromEntries(new FormData(filtersForm).entries());
    const search = String(formValues.search || '').toLowerCase();
    return incidents.filter((incident) => {
      const matchesSearch = !search || [incident.incident_id, incident.oem, incident.customer_complaint, incident.vehicle_variant, incident.ecu_part_number].join(' ').toLowerCase().includes(search);
      const matchesSeverity = !formValues.severity || incident.severity === formValues.severity;
      const matchesStatus = !formValues.status || incident.status === formValues.status;
      const matchesOem = !formValues.oem || incident.oem === formValues.oem;
      return matchesSearch && matchesSeverity && matchesStatus && matchesOem;
    });
  }

  function renderMetrics() {
    const today = new Date();
    const source = applyFilters();
    const overdue = source.filter((incident) => incident.target_date && new Date(incident.target_date) < today && incident.status !== 'Closed').length;
    const summary = [
      ['My Total Incidents', source.length],
      ['Open Incidents', source.filter((item) => item.status !== 'Closed').length],
      ['Critical Incidents', source.filter((item) => item.severity === 'Critical').length],
      ['Pending Validation', source.filter((item) => item.status === 'Validation').length],
      ['Closed Incidents', source.filter((item) => item.status === 'Closed').length],
      ['Overdue Incidents', overdue],
    ];
    metrics.innerHTML = summary.map(([label, value]) => `<div class="metric-card"><span>${label}</span><strong>${value}</strong></div>`).join('');
  }

  function renderTable() {
    const rows = applyFilters();
    if (!rows.length) {
      tableBody.innerHTML = '<tr><td colspan="8"><div class="empty-state">No incidents are currently assigned to you.</div></td></tr>';
      return;
    }
    tableBody.innerHTML = rows.map((incident) => `
      <tr data-id="${incident.incident_id}">
        <td>${window.EFQUI.escapeHtml(incident.incident_id)}</td>
        <td>${window.EFQUI.escapeHtml(incident.oem)}</td>
        <td>${window.EFQUI.escapeHtml(incident.severity)}</td>
        <td>${window.EFQUI.escapeHtml(incident.issue_type)}</td>
        <td>${window.EFQUI.escapeHtml(incident.customer_complaint)}</td>
        <td>${window.EFQUI.escapeHtml(incident.status)}</td>
        <td>${window.EFQUI.escapeHtml(window.EFQUI.formatDate(incident.target_date))}</td>
        <td>${window.EFQUI.escapeHtml(window.EFQUI.formatDateTime(incident.updated_at))}</td>
      </tr>
    `).join('');
    tableBody.querySelectorAll('tr[data-id]').forEach((row) => row.addEventListener('click', () => loadDetail(row.dataset.id)));
  }

  async function loadDetail(incidentId) {
    currentIncidentId = incidentId;
    const detail = await window.EFQApi.get(`/api/custodian/incidents/${incidentId}`);
    const incident = detail.incident;
    const resolution = detail.resolution || {};
    emptyPanel.hidden = true;
    detailPanel.hidden = false;
    detailPanel.innerHTML = `
      <div class="card">
        <div class="section-head">
          <div>
            <div class="page-title">${window.EFQUI.escapeHtml(incident.incident_id)}</div>
            <div class="muted">${window.EFQUI.escapeHtml(incident.status)} · ${window.EFQUI.escapeHtml(incident.oem)} · ${window.EFQUI.escapeHtml(incident.severity)}</div>
          </div>
          <span class="status-badge">Assigned to ${window.EFQUI.escapeHtml(incident.custodian_name)}</span>
        </div>
      </div>
      <div class="detail-layout">
        <div class="detail-stack">
          <div class="card">
            <h3 class="card-title">Original Incident Information</h3>
            <div class="info-grid">
              <div><strong>Customer Complaint</strong><p>${window.EFQUI.escapeHtml(incident.customer_complaint)}</p></div>
              <div><strong>Issue Type</strong><p>${window.EFQUI.escapeHtml(incident.issue_type)}</p></div>
              <div><strong>Dealer</strong><p>${window.EFQUI.escapeHtml(`${incident.dealer_name}, ${incident.dealer_location}`)}</p></div>
              <div><strong>Dealer Contact</strong><p>${window.EFQUI.escapeHtml(incident.dealer_contact)}</p></div>
              <div><strong>Vehicle</strong><p>${window.EFQUI.escapeHtml(`${incident.vehicle_model} / ${incident.vehicle_variant}`)}</p></div>
              <div><strong>ECU</strong><p>${window.EFQUI.escapeHtml(`${incident.ecu_name} (${incident.ecu_part_number})`)}</p></div>
            </div>
            <p><strong>Description</strong></p>
            <p>${window.EFQUI.escapeHtml(incident.description)}</p>
          </div>
          <div class="card">
            <h3 class="card-title">Activity History</h3>
            <div class="activity-list">
              ${(detail.activities || []).map((activity) => `
                <div class="activity-item">
                  <strong>${window.EFQUI.escapeHtml(activity.action)}</strong>
                  <div class="muted">${window.EFQUI.escapeHtml(activity.user_name)} · ${window.EFQUI.escapeHtml(window.EFQUI.formatDateTime(activity.timestamp))}</div>
                </div>
              `).join('') || '<div class="empty-state">No activity history recorded yet.</div>'}
            </div>
          </div>
        </div>
        <div class="card">
          <h3 class="card-title">Investigation & Solution</h3>
          <form id="resolutionForm" class="grid-form">
            <div class="field"><label for="investigation_details">Investigation Details</label><textarea id="investigation_details" name="investigation_details">${window.EFQUI.escapeHtml(resolution.investigation_details || '')}</textarea></div>
            <div class="field"><label for="root_cause">Root Cause</label><textarea id="root_cause" name="root_cause">${window.EFQUI.escapeHtml(resolution.root_cause || '')}</textarea></div>
            <div class="field"><label for="recommendation">Recommendation</label><textarea id="recommendation" name="recommendation">${window.EFQUI.escapeHtml(resolution.recommendation || '')}</textarea></div>
            <div class="field"><label for="proposed_solution">Proposed Solution</label><textarea id="proposed_solution" name="proposed_solution">${window.EFQUI.escapeHtml(resolution.proposed_solution || '')}</textarea></div>
            <div class="field"><label for="corrective_action">Corrective Action</label><textarea id="corrective_action" name="corrective_action">${window.EFQUI.escapeHtml(resolution.corrective_action || '')}</textarea></div>
            <div class="field"><label for="preventive_action">Preventive Action</label><textarea id="preventive_action" name="preventive_action">${window.EFQUI.escapeHtml(resolution.preventive_action || '')}</textarea></div>
            <div class="grid-form two-column">
              <div class="field"><label for="validation_method">Validation Method</label><input id="validation_method" name="validation_method" value="${window.EFQUI.escapeHtml(resolution.validation_method || '')}"></div>
              <div class="field"><label for="validation_result">Validation Result</label><select id="validation_result" name="validation_result"><option ${resolution.validation_result === 'Not Tested' ? 'selected' : ''}>Not Tested</option><option ${resolution.validation_result === 'Pass' ? 'selected' : ''}>Pass</option><option ${resolution.validation_result === 'Fail' ? 'selected' : ''}>Fail</option><option ${resolution.validation_result === 'Conditional Pass' ? 'selected' : ''}>Conditional Pass</option></select></div>
              <div class="field"><label for="validation_date">Validation Date</label><input id="validation_date" type="date" name="validation_date" value="${window.EFQUI.escapeHtml(resolution.validation_date || '')}"></div>
              <div class="field"><label for="target_date">Target Date</label><input id="target_date" type="date" name="target_date" value="${window.EFQUI.escapeHtml(resolution.target_date || '')}"></div>
              <div class="field"><label for="resolution_status">Resolution Status</label><select id="resolution_status" name="resolution_status"><option ${resolution.resolution_status === 'Not Started' ? 'selected' : ''}>Not Started</option><option ${resolution.resolution_status === 'Investigation' ? 'selected' : ''}>Investigation</option><option ${resolution.resolution_status === 'Root Cause Identified' ? 'selected' : ''}>Root Cause Identified</option><option ${resolution.resolution_status === 'Action In Progress' ? 'selected' : ''}>Action In Progress</option><option ${resolution.resolution_status === 'Validation' ? 'selected' : ''}>Validation</option><option ${resolution.resolution_status === 'Closed' ? 'selected' : ''}>Closed</option></select></div>
            </div>
            <div class="field"><label for="remarks">Remarks</label><textarea id="remarks" name="remarks">${window.EFQUI.escapeHtml(resolution.remarks || '')}</textarea></div>
            <div class="form-actions"><button type="submit" class="primary">Save Investigation &amp; Solution</button></div>
          </form>
        </div>
      </div>
    `;

    document.getElementById('resolutionForm').addEventListener('submit', async (event) => {
      event.preventDefault();
      const button = event.currentTarget.querySelector('button[type="submit"]');
      const payload = Object.fromEntries(new FormData(event.currentTarget).entries());
      window.EFQUI.setButtonLoading(button, true, 'Saving solution...');
      try {
        await window.EFQApi.put(`/api/custodian/incidents/${incidentId}/resolution`, payload);
        window.EFQUI.showToast('Investigation and solution saved successfully.', 'success');
        await loadIncidents();
        await loadDetail(incidentId);
      } catch (error) {
        window.EFQUI.showToast(error.message, 'error');
      } finally {
        window.EFQUI.setButtonLoading(button, false);
      }
    });
  }

  filtersForm.addEventListener('input', () => {
    renderMetrics();
    renderTable();
  });
  await loadIncidents();
});
