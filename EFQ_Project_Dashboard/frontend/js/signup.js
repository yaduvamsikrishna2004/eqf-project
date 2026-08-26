document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('signupForm');
  const signInLink = document.getElementById('signinLink');
  signInLink?.addEventListener('click', (event) => {
    event.preventDefault();
    window.location.href = '/signin';
  });

  form?.addEventListener('submit', async (event) => {
    event.preventDefault();
    const submitButton = form.querySelector('button[type="submit"]');
    const payload = Object.fromEntries(new FormData(form).entries());
    window.EFQUI.setButtonLoading(submitButton, true, 'Creating account...');
    try {
      const response = await window.EFQApi.post('/api/auth/signup', payload);
      window.EFQUI.showToast(`Account created for ${response.user.full_name}. Please sign in.`, 'success');
      form.reset();
      window.setTimeout(() => {
        window.location.href = '/signin';
      }, 800);
    } catch (error) {
      window.EFQUI.showToast(error.message, 'error');
    } finally {
      window.EFQUI.setButtonLoading(submitButton, false);
    }
  });
});
