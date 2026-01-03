import { authAPI, getStoredAuth, setStoredAuth, clearStoredAuth } from './api/apiService';

export const authProvider = {
  login: async ({ username, password }) => {
    try {
      const data = await authAPI.login(username, password);
      const { token, account_role } = data;

      // Store token and account role
      setStoredAuth(token, account_role);

      return Promise.resolve();
    } catch (error) {
      return Promise.reject(error);
    }
  },

  logout: () => {
    clearStoredAuth();
    return Promise.resolve();
  },

  checkAuth: () => {
    const { token } = getStoredAuth();
    return token ? Promise.resolve() : Promise.reject();
  },

  checkError: (error) => {
    const status = error.status;
    if (status === 401 || status === 403) {
      clearStoredAuth();
      return Promise.reject();
    }
    return Promise.resolve();
  },

  getIdentity: () => {
    const { token, accountRole } = getStoredAuth();
    if (token) {
      return Promise.resolve({
        id: 'user',
        fullName: accountRole || 'User',
        role: accountRole,
      });
    }
    return Promise.reject();
  },

  getPermissions: () => {
    const { accountRole } = getStoredAuth();
    // Return permissions based on account role
    if (accountRole === 'admin') {
      return Promise.resolve({
        canCreate: true,
        canEdit: true,
        canDelete: true,
        canExport: true,
        canImport: true,
      });
    } else if (accountRole === 'corporate_admin') {
      return Promise.resolve({
        canCreate: false,
        canEdit: true, // Can only edit job role
        canDelete: false,
        canExport: false,
        canImport: false,
      });
    } else {
      return Promise.resolve({
        canCreate: false,
        canEdit: false,
        canDelete: false,
        canExport: false,
        canImport: false,
      });
    }
  },
};

