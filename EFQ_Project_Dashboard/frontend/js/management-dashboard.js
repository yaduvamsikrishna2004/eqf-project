document.addEventListener('DOMContentLoaded', async () => {
  const user = await window.EFQNavigation.bootProtectedPage(
    'management-dashboard',
    'Management Dashboard',
    'Monitor enterprise EFQ risk, throughput, and custodian performance from live workbook data.'
  );
  if (!user) return;

  const charts = {};
  const filtersForm = document.getElementById('managementFilters');
  const metricHost = document.getElementById('managementMetrics');
  const incidentBody = document.getElementById('managementIncidentRows');
  const insightsHost = document.getElementById('managementInsights');
  const performanceBody = document.getElementById('resolutionPerformanceRows');

  function currentQuery() {
    return new URLSearchParams(new FormData(filtersForm)).toString();
  }

  async function populateLookupFilters() {
    const [oems, custodians] = await Promise.all([
      window.EFQApi.get('/api/lookups/oems'),
      window.EFQApi.get('/api/users/custodians'),
    ]);
    document.getElementById('filterOem').innerHTML += oems.map((row) => `<option value="${row.OEM}">${row.OEM}</option>`).join('');
    document.getElementById('filterCustodian').innerHTML += custodians.map((row) => `<option value="${row.full_name}">${row.full_name}</option>`).join('');
  }

  function renderMetrics(summary) {
    const cards = [
      ['Total Incidents', summary.total_incidents],
      ['Open Incidents', summary.open_incidents],
      ['Closed Incidents', summary.closed_incidents],
      ['Critical Incidents', summary.critical_incidents],
      ['Overdue Incidents', summary.overdue_incidents],
      ['Average Resolution Days', summary.average_resolution_days ?? 'N/A'],
    ];
    metricHost.innerHTML = cards.map(([label, value]) => `<div class="metric-card"><span>${label}</span><strong>${value}</strong></div>`).join('');
  }

  function upsertChart(canvasId, config) {
    const context = document.getElementById(canvasId).getContext('2d');
    if (charts[canvasId]) charts[canvasId].destroy();
    charts[canvasId] = new Chart(context, config);
  }

  function renderCharts(chartData) {
    upsertChart('oemChart', { type: 'bar', data: { labels: chartData.oem_wise_incidents.labels, datasets: [{ label: 'Incidents', data: chartData.oem_wise_incidents.data, backgroundColor: '#2f7cc0' }] } });
    upsertChart('severityChart', { type: 'doughnut', data: { labels: chartData.severity_distribution.labels, datasets: [{ data: chartData.severity_distribution.data, backgroundColor: ['#c23a32', '#c9871a', '#2f7cc0', '#1f8b4c'] }] } });
    upsertChart('statusChart', { type: 'doughnut', data: { labels: chartData.status_distribution.labels, datasets: [{ data: chartData.status_distribution.data, backgroundColor: ['#0f4c81', '#2f7cc0', '#c9871a', '#1f8b4c', '#c23a32', '#96a5b5'] }] } });
    upsertChart('issueTypeChart', { type: 'bar', data: { labels: chartData.issue_type_distribution.labels, datasets: [{ label: 'Incidents', data: chartData.issue_type_distribution.data, backgroundColor: '#0f4c81' }] } });
    upsertChart('monthlyTrendChart', { type: 'line', data: { labels: chartData.monthly_incident_trend.labels, datasets: [{ label: 'Monthly Incidents', data: chartData.monthly_incident_trend.data, borderColor: '#2f7cc0', backgroundColor: 'rgba(47,124,192,0.18)', fill: true, tension: 0.3 }] } });
    upsertChart('custodianWorkloadChart', { type: 'bar', data: { labels: chartData.custodian_workload.labels, datasets: [{ label: 'Active Load', data: chartData.custodian_workload.data, backgroundColor: '#1f8b4c' }] } });
  }

  function renderInsights(items) {
    insightsHost.innerHTML = items.map((item) => `<li>${window.EFQUI.escapeHtml(item)}</li>`).join('');
  }

  function renderPerformance(items) {
    performanceBody.innerHTML = items.map((item) => `
      <tr>
        <td>${window.EFQUI.escapeHtml(item.custodian)}</td>
        <td>${item.total}</td>
        <td>${item.open}</td>
        <td>${item.closed}</td>
        <td>${item.critical}</td>
        <td>${item.average_resolution_days ?? 'N/A'}</td>
      </tr>
    `).join('') || '<tr><td colspan="6"><div class="empty-state">No workload metrics available.</div></td></tr>';
  }

  function renderIncidents(items) {
    incidentBody.innerHTML = items.map((item) => `
      <tr>
        <td>${window.EFQUI.escapeHtml(item.IncidentID)}</td>
        <td>${window.EFQUI.escapeHtml(item.OEM)}</td>
        <td>${window.EFQUI.escapeHtml(item.Severity)}</td>
        <td>${window.EFQUI.escapeHtml(item.CustodianName)}</td>
        <td>${window.EFQUI.escapeHtml(item.Status)}</td>
        <td>${window.EFQUI.escapeHtml(item.IssueType)}</td>
        <td>${window.EFQUI.escapeHtml(window.EFQUI.formatDateTime(item.CreatedAt))}</td>
        <td>${window.EFQUI.escapeHtml(window.EFQUI.formatDateTime(item.UpdatedAt))}</td>
      </tr>
    `).join('') || '<tr><td colspan="8"><div class="empty-state">No incidents found for the selected filters.</div></td></tr>';
  }

  async function refreshDashboard() {
    try {
      const query = currentQuery();
      const [analytics, incidents] = await Promise.all([
        window.EFQApi.get(`/api/management/analytics?${query}`),
        window.EFQApi.get(`/api/management/incidents?${query}`),
      ]);
      renderMetrics(analytics.summary);
      renderCharts(analytics.charts);
      renderInsights(analytics.insights);
      renderPerformance(analytics.resolution_performance);
      renderIncidents(incidents);
    } catch (error) {
      window.EFQUI.showToast(error.message, 'error');
    }
  }

  filtersForm.addEventListener('input', () => refreshDashboard());
  await populateLookupFilters();
  await refreshDashboard();
});
