const MODULE_ACCESS = {
  'incident-reporting': ['Admin', 'Manager', 'Custodian', 'Other'],
  'custodian-dashboard': ['Admin', 'Custodian'],
  'management-dashboard': ['Admin', 'Manager'],
};

function initialsFromName(name) {
  return String(name || 'User')
    .split(' ')
    .map((part) => part[0])
    .join('')
    .slice(0, 2)
    .toUpperCase();
}

function injectShell(user, pageKey, title, subtitle) {
  const sidebar = document.getElementById('sidebarNav');
  const userPill = document.getElementById('userPill');
  const pageTitle = document.getElementById('pageTitle');
  const pageSubtitle = document.getElementById('pageSubtitle');

  if (pageTitle) pageTitle.textContent = title;
  if (pageSubtitle) pageSubtitle.textContent = subtitle;

  if (userPill) {
    userPill.innerHTML = `
      <span class="user-avatar">${initialsFromName(user.full_name)}</span>
      <span>
        <strong>${window.EFQUI.escapeHtml(user.full_name)}</strong><br>
        <span class="muted">${window.EFQUI.escapeHtml(user.role)}</span>
      </span>
      <button id="signOutButton" class="ghost">Sign Out</button>
    `;
    document.getElementById('signOutButton').addEventListener('click', async () => {
      try {
        await window.EFQAuth.signOut();
      } catch (error) {
        window.EFQUI.showToast(error.message, 'error');
      } finally {
        window.location.href = '/signin';
      }
    });
  }

  if (!sidebar) return;
  const navItems = [
    { key: 'incident-reporting', label: 'Incident Reporting', href: '/incident-reporting' },
    { key: 'custodian-dashboard', label: 'Custodian Dashboard', href: '/custodian-dashboard' },
    { key: 'management-dashboard', label: 'Management Dashboard', href: '/management-dashboard' },
  ].filter((item) => MODULE_ACCESS[item.key].includes(user.role));

  sidebar.innerHTML = navItems
    .map((item) => `<a class="nav-link ${item.key === pageKey ? 'active' : ''}" href="${item.href}">${item.label}</a>`)
    .join('');
}

async function bootProtectedPage(pageKey, title, subtitle) {
  try {
    const user = await window.EFQAuth.getCurrentUser();
    if (!MODULE_ACCESS[pageKey].includes(user.role)) {
      window.location.href = window.EFQAuth.defaultRouteForRole(user.role);
      return null;
    }
    injectShell(user, pageKey, title, subtitle);
    return user;
  } catch (error) {
    window.location.href = '/signin';
    return null;
  }
}

window.EFQNavigation = { bootProtectedPage };
