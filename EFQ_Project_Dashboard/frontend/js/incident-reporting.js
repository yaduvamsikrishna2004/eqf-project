document.addEventListener('DOMContentLoaded', async () => {
  const user = await window.EFQNavigation.bootProtectedPage(
    'incident-reporting',
    'Incident Reporting',
    'Create a new field quality incident with backend-generated EFQ tracking.'
  );
  if (!user) return;

  const form = document.getElementById('incidentForm');
  const oemSelect = document.getElementById('oem');
  const custodianSelect = document.getElementById('custodian_ntid');
  const ecuSelect = document.getElementById('ecu_name');
  const ecuPartInput = document.getElementById('ecu_part_number');
  const dateInput = document.getElementById('date');
  const clearButton = document.getElementById('clearIncidentForm');
  const suggestionList = document.getElementById('complaintSuggestions');
  const resultPanel = document.getElementById('incidentResult');
  dateInput.value = new Date().toISOString().split('T')[0];

  try {
    const [oems, custodians, ecus, complaints, phases] = await Promise.all([
      window.EFQApi.get('/api/lookups/oems'),
      window.EFQApi.get('/api/users/custodians'),
      window.EFQApi.get('/api/lookups/ecus'),
      window.EFQApi.get('/api/lookups/complaints'),
      window.EFQApi.get('/api/lookups/detection-phases'),
    ]);

    oemSelect.innerHTML += oems.map((row) => `<option value="${row.OEM}">${row.OEM}</option>`).join('');
    custodianSelect.innerHTML += custodians.map((row) => `<option value="${row.ntid}">${row.full_name} (${row.ntid})</option>`).join('');
    ecuSelect.innerHTML += ecus.map((row) => `<option value="${row.ECUName}" data-part="${row.ECUPartNumber}">${row.ECUName}</option>`).join('');
    suggestionList.innerHTML = complaints.map((row) => `<span class="pill">${window.EFQUI.escapeHtml(row.ComplaintDescription)}</span>`).join('');
    document.getElementById('diagnosticPhaseHints').innerHTML = phases.map((row) => `<span class="pill">${window.EFQUI.escapeHtml(row.PhaseName)}</span>`).join('');
  } catch (error) {
    window.EFQUI.showToast(error.message, 'error');
  }

  ecuSelect.addEventListener('change', () => {
    const option = ecuSelect.selectedOptions[0];
    ecuPartInput.value = option?.dataset.part || '';
  });

  clearButton.addEventListener('click', () => {
    form.reset();
    dateInput.value = new Date().toISOString().split('T')[0];
    resultPanel.innerHTML = '';
  });

  async function submitIncident(draft) {
    const submitButton = draft ? document.getElementById('saveDraftButton') : document.getElementById('submitIncidentButton');
    const formData = new FormData(form);
    const payload = Object.fromEntries(formData.entries());
    payload.kilometer_reading = Number(payload.kilometer_reading || 0);
    payload.draft = draft;
    window.EFQUI.setButtonLoading(submitButton, true, draft ? 'Saving draft...' : 'Saving incident...');
    try {
      const incident = await window.EFQApi.post('/api/incidents', payload);
      const successMessage = draft ? `Draft ${incident.incident_id} saved successfully.` : `Incident ${incident.incident_id} created successfully.`;
      window.EFQUI.showToast(successMessage, 'success');
      resultPanel.innerHTML = `
        <div class="card">
          <strong>${window.EFQUI.escapeHtml(incident.incident_id)}</strong>
          <p class="muted">${window.EFQUI.escapeHtml(successMessage)}</p>
          <p class="muted">Assigned custodian: ${window.EFQUI.escapeHtml(incident.custodian_name)}</p>
        </div>
      `;
      if (!draft) form.reset();
      dateInput.value = new Date().toISOString().split('T')[0];
    } catch (error) {
      window.EFQUI.showToast(error.message, 'error');
    } finally {
      window.EFQUI.setButtonLoading(submitButton, false);
    }
  }

  document.getElementById('saveDraftButton').addEventListener('click', () => submitIncident(true));
  document.getElementById('submitIncidentButton').addEventListener('click', () => submitIncident(false));
});
