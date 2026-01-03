/**
 * Centralized API Service
 * Contains all API configuration, helper functions, and API call functions
 */

// API Configuration
export const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

//Get authentication headers for API requests

export const getAuthHeaders = () => {
  const token = localStorage.getItem('token');
  return {
    'Content-Type': 'application/json',
    'Authorization': token ? `Bearer ${token}` : '',
  };
};

//Get token and role from localStorage

export const getStoredAuth = () => {
  const token = localStorage.getItem('token');
  const accountRole = localStorage.getItem('account_role');
  return { token, accountRole };
};

//Store auth in localStorage

export const setStoredAuth = (token, accountRole) => {
  localStorage.setItem('token', token);
  localStorage.setItem('account_role', accountRole);
};

//Clear auth from localStorage

export const clearStoredAuth = () => {
  localStorage.removeItem('token');
  localStorage.removeItem('account_role');
};

//Global error handler for API requests
//Handles network errors, HTTP errors, and parsing errors

export const fetchJson = (url, options = {}) => {
  return fetch(url, {
    ...options,
    headers: {
      ...getAuthHeaders(),
      ...options.headers,
    },
  })
    .then(async (response) => {
      const text = await response.text();
      let json;
      
      // Try to parse JSON response
      try {
        json = text ? JSON.parse(text) : {};
      } catch (e) {
        // If parsing fails, create a structured error object
        json = { 
          message: text || 'Invalid response format',
          detail: text || 'Invalid response format'
        };
      }

      // Handle HTTP errors
      if (!response.ok) {
        const error = {
          status: response.status,
          statusText: response.statusText,
          message: json.detail || json.message || `HTTP Error ${response.status}`,
          body: json,
          url: url,
        };

        // Add specific error messages based on status code
        switch (response.status) {
          case 400:
            error.message = json.detail || json.message || 'Bad request. Please check your input.';
            break;
          case 401:
            error.message = 'Authentication required. Please log in again.';
            break;
          case 403:
            error.message = json.detail || json.message || 'You do not have permission to perform this action.';
            break;
          case 404:
            error.message = json.detail || json.message || 'Resource not found.';
            break;
          case 422:
            error.message = json.detail || json.message || 'Validation error. Please check your input.';
            // Handle validation errors with field-specific messages
            if (json.detail && Array.isArray(json.detail)) {
              error.validationErrors = json.detail;
            }
            break;
          case 500:
            error.message = json.detail || json.message || 'Internal server error. Please try again later.';
            break;
          case 503:
            error.message = 'Service unavailable. Please try again later.';
            break;
          default:
            error.message = json.detail || json.message || `An error occurred (${response.status})`;
        }

        return Promise.reject(error);
      }

      return { status: response.status, headers: response.headers, json };
    })
    .catch((error) => {
      // Handle network errors, timeouts, and other fetch failures
      if (error.name === 'TypeError' && error.message.includes('fetch')) {
        return Promise.reject({
          status: 0,
          message: 'Network error. Please check your connection and try again.',
          body: { error: error.message },
          url: url,
        });
      }
      
      // Re-throw if it's already a structured error
      if (error.status !== undefined) {
        return Promise.reject(error);
      }
      
      // Handle other unexpected errors
      return Promise.reject({
        status: 0,
        message: error.message || 'An unexpected error occurred',
        body: { error: error.message },
        url: url,
      });
    });
};

//Authentication API calls

export const authAPI = {
  //Login user
  //@param {string} username - User email
  //@param {string} password - User password
  //@returns {Promise<{token: string, account_role: string}>}

  login: async (username, password) => {
    const response = await fetch(`${API_URL}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username, password }),
    });

    if (!response.ok) {
      throw new Error('Login failed');
    }

    const data = await response.json();
    return data;
  },
};

//Users API calls

export const usersAPI = {
  //Upload CSV file to bulk create users
  //@param {File} file - CSV file to upload
  //@returns {Promise<{total_rows: number, users_created: number, errors: Array}>}

  uploadCSV: async (file) => {
    const token = localStorage.getItem('token');
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_URL}/users/upload-csv`, {
      method: 'POST',
      headers: {
        'Authorization': token ? `Bearer ${token}` : '',
      },
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Upload failed');
    }

    const data = await response.json();
    return data;
  },

  //Export users as CSV
  //@param {Object} filters - Filter parameters (role, status, account_role, search)
  //@param {Object} sort - Sort parameters (field, order)
  //@returns {Promise<Blob>} - CSV file blob

  exportCSV: async (filters = {}, sort = {}) => {
    const token = localStorage.getItem('token');
    
    // Build query params from filters and sort
    const params = new URLSearchParams();
    
    // Helper function to safely get string value
    const getStringValue = (value) => {
      if (value == null) return null;
      const str = String(value).trim();
      return str || null;
    };
    
    // Add filters - only add non-empty string values
    const roleValue = getStringValue(filters?.role);
    if (roleValue) {
      params.append('role', roleValue);
    }
    
    const statusValue = getStringValue(filters?.status);
    if (statusValue) {
      params.append('status', statusValue);
    }
    
    const accountRoleValue = getStringValue(filters?.account_role);
    if (accountRoleValue) {
      params.append('account_role', accountRoleValue);
    }
    
    const searchValue = getStringValue(filters?.search);
    if (searchValue) {
      params.append('search', searchValue);
    }
    
    // Add sort - only if sortField exists and is valid
    const sortField = getStringValue(sort?.field);
    if (sortField) {
      params.append('sort_field', sortField);
      const sortOrderRaw = sort?.order || 'DESC';
      const sortOrder = String(sortOrderRaw).toLowerCase();
      if (sortOrder === 'asc' || sortOrder === 'desc') {
        params.append('sort_order', sortOrder);
      } else {
        params.append('sort_order', 'desc');
      }
    }

    // Build URL with query params
    const queryString = params.toString();
    const url = `${API_URL}/users/export-csv${queryString ? `?${queryString}` : ''}`;
    
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Authorization': token ? `Bearer ${token}` : '',
      },
    });

    // Check if response is ok before processing
    if (!response.ok) {
      let errorMessage = 'Export failed';
      const contentType = response.headers.get('content-type');
      
      // Try to parse error response
      if (contentType && contentType.includes('application/json')) {
        try {
          const error = await response.json();
          errorMessage = error.detail || error.message || `HTTP ${response.status}: ${response.statusText}`;
        } catch (e) {
          errorMessage = `HTTP ${response.status}: ${response.statusText}`;
        }
      } else {
        // If not JSON, try to get text
        try {
          const text = await response.text();
          errorMessage = text || `HTTP ${response.status}: ${response.statusText}`;
        } catch (e) {
          errorMessage = `HTTP ${response.status}: ${response.statusText}`;
        }
      }
      throw new Error(errorMessage);
    }

    // Verify content type is CSV before processing as blob
    const contentType = response.headers.get('content-type');
    if (contentType && !contentType.includes('text/csv') && !contentType.includes('application/octet-stream')) {
      // If not CSV, might be an error response
      const text = await response.text();
      throw new Error(`Unexpected response type: ${contentType}. Response: ${text.substring(0, 200)}`);
    }

    // Return the blob
    const blob = await response.blob();
    return blob;
  },
};

