document.addEventListener('DOMContentLoaded', async () => {
  try {
    const user = await window.EFQAuth.getCurrentUser();
    window.location.href = window.EFQAuth.defaultRouteForRole(user.role);
    return;
  } catch (error) {
    // stay on sign-in page
  }

  const form = document.getElementById('signinForm');
  form?.addEventListener('submit', async (event) => {
    event.preventDefault();
    const submitButton = form.querySelector('button[type="submit"]');
    const payload = Object.fromEntries(new FormData(form).entries());
    window.EFQUI.setButtonLoading(submitButton, true, 'Signing in...');
    try {
      const response = await window.EFQApi.post('/api/auth/signin', payload);
      window.EFQUI.showToast(`Welcome back, ${response.user.full_name}.`, 'success');
      window.location.href = window.EFQAuth.defaultRouteForRole(response.user.role);
    } catch (error) {
      window.EFQUI.showToast(error.message, 'error');
    } finally {
      window.EFQUI.setButtonLoading(submitButton, false);
    }
  });
});
