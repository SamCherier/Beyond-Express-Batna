/**
 * Force Logout Utility
 * AGGRESSIVE logout that clears ALL auth data and redirects
 * Use this when standard logout fails or creates auth loops
 */

export const forceLogout = () => {
  console.log('🔴 FORCE LOGOUT INITIATED');

  try {
    // STEP 1: Clear localStorage
    localStorage.clear();
    console.log('✅ localStorage cleared');

    // STEP 2: Clear sessionStorage
    sessionStorage.clear();
    console.log('✅ sessionStorage cleared');

    // STEP 3: NUKE ALL COOKIES (multiple paths and domains)
    const cookies = document.cookie.split(';');
    
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i];
      const eqPos = cookie.indexOf('=');
      const name = eqPos > -1 ? cookie.substr(0, eqPos).trim() : cookie.trim();
      
      // Delete cookie for multiple paths and domains
      const paths = ['/', '/dashboard', '/api'];
      const domains = [window.location.hostname, `.${window.location.hostname}`];
      
      paths.forEach(path => {
        domains.forEach(domain => {
          // Set cookie to expired date
          document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=${path}; domain=${domain}`;
          document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=${path}`;
        });
      });
      
      // Also try without domain
      document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/`;
    }
    
    console.log('✅ All cookies nuked');

    // STEP 4: Hard redirect (replace to destroy history)
    console.log('🔄 Redirecting to /login...');
    
    // Use setTimeout to ensure all cleanup completes
    setTimeout(() => {
      window.location.replace('/login');
    }, 100);

  } catch (error) {
    console.error('❌ Error during force logout:', error);
    // Even if there's an error, force redirect
    window.location.replace('/login');
  }
};

/**
 * Safe logout with confirmation
 * Wrapper around forceLogout with user confirmation
 */
export const safeLogout = () => {
  if (window.confirm('Êtes-vous sûr de vouloir vous déconnecter ?')) {
    forceLogout();
  }
};

export default { forceLogout, safeLogout };
