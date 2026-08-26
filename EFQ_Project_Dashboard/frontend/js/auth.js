function defaultRouteForRole(role) {
  if (role === 'Admin' || role === 'Manager') return '/management-dashboard';
  if (role === 'Custodian') return '/custodian-dashboard';
  return '/incident-reporting';
}

async function getCurrentUser() {
  const payload = await window.EFQApi.get('/api/auth/me');
  return payload.user;
}

async function signOut() {
  await window.EFQApi.post('/api/auth/signout', {});
}

window.EFQAuth = { defaultRouteForRole, getCurrentUser, signOut };
