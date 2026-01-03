import { API_URL, fetchJson } from './api/apiService';


 //Convert react-admin filter object to query string parameters
const buildQueryParams = (params) => {
  const { pagination, sort, filter } = params;
  const queryParams = new URLSearchParams();

  // Pagination: react-admin uses 1-based page, backend expects 1-based
  if (pagination) {
    queryParams.append('page', pagination.page || 1);
    queryParams.append('page_size', pagination.perPage || 10);
  }

  // Sorting: convert react-admin sort format to backend format
  // React-admin uses 'ASC'/'DESC', backend expects 'asc'/'desc'
  if (sort && sort.field) {
    queryParams.append('sort_field', sort.field);
    const sortOrder = (sort.order || 'ASC').toLowerCase();
    queryParams.append('sort_order', sortOrder);
  }

  // Filters: add all filter parameters
  if (filter) {
    Object.keys(filter).forEach((key) => {
      const value = filter[key];
      // Skip null, undefined, and empty string values
      if (value !== null && value !== undefined && value !== '') {
        queryParams.append(key, encodeURIComponent(value));
      }
    });
  }

  return queryParams.toString();
};


// React-admin data provider with full CRUD support

export const dataProvider = {

  //Get a list of resources with pagination, sorting, and filtering
  getList: async (resource, params) => {
    try {
      const queryString = buildQueryParams(params);
      const url = `${API_URL}/${resource}${queryString ? `?${queryString}` : ''}`;
      
      const { json } = await fetchJson(url);
      
      // Backend should returns- { items: [...], total: number, page: number, page_size: number }
      return {
        data: json.items || [],
        total: json.total || 0,
      };
    } catch (error) {

      throw new Error(`Failed to fetch ${resource} list: ${error.message}`);
    }
  },

  
  //Get a single resource by ID
  getOne: async (resource, params) => {
    try {
      const { json } = await fetchJson(`${API_URL}/${resource}/${params.id}`);
      return { data: json };
    } catch (error) {
      throw new Error(`Failed to fetch ${resource} with id ${params.id}: ${error.message}`);
    }
  },


  //Get multiple resources by their IDs
  getMany: async (resource, params) => {
    try {
      const promises = params.ids.map((id) =>
        fetchJson(`${API_URL}/${resource}/${id}`)
      );
      const responses = await Promise.all(promises);
      return {
        data: responses.map(({ json }) => json),
      };
    } catch (error) {
      throw new Error(`Failed to fetch multiple ${resource}: ${error.message}`);
    }
  },

  //Get resources referenced by another resource
  getManyReference: async (resource, params) => {
    try {
      // Add the reference filter to the existing filters
      const filters = {
        ...params.filter,
        [params.target]: params.id,
      };
      
      return dataProvider.getList(resource, {
        ...params,
        filter: filters,
      });
    } catch (error) {
      throw new Error(`Failed to fetch ${resource} references: ${error.message}`);
    }
  },

 //Create a new resource
  create: async (resource, params) => {
    try {
      const { json } = await fetchJson(`${API_URL}/${resource}`, {
        method: 'POST',
        body: JSON.stringify(params.data),
      });
      return { data: json };
    } catch (error) {
      // Provide more context for validation errors
      if (error.status === 400 || error.status === 422) {
        throw new Error(`Validation error: ${error.message}`);
      }
      throw new Error(`Failed to create ${resource}: ${error.message}`);
    }
  },

  //Update a resource by ID
  update: async (resource, params) => {
    try {
      const { json } = await fetchJson(`${API_URL}/${resource}/${params.id}`, {
        method: 'PUT',
        body: JSON.stringify(params.data),
      });
      return { data: json };
    } catch (error) {
      // Provide more context for validation errors
      if (error.status === 400 || error.status === 422) {
        throw new Error(`Validation error: ${error.message}`);
      }
      if (error.status === 403) {
        throw new Error(`Permission denied: ${error.message}`);
      }
      throw new Error(`Failed to update ${resource} with id ${params.id}: ${error.message}`);
    }
  },

  //pdate multiple resources by their IDs
  updateMany: async (resource, params) => {
    try {
      const promises = params.ids.map((id) =>
        fetchJson(`${API_URL}/${resource}/${id}`, {
          method: 'PUT',
          body: JSON.stringify(params.data),
        })
      );
      const responses = await Promise.all(promises);
      return {
        data: responses.map(({ json }) => json.id || json),
      };
    } catch (error) {
      throw new Error(`Failed to update multiple ${resource}: ${error.message}`);
    }
  },

  //Delete a resource by ID
  delete: async (resource, params) => {
    try {
      await fetchJson(`${API_URL}/${resource}/${params.id}`, {
        method: 'DELETE',
      });
      return { data: { id: params.id } };
    } catch (error) {
      if (error.status === 403) {
        throw new Error(`Permission denied: ${error.message}`);
      }
      if (error.status === 404) {
        throw new Error(`Resource not found: ${error.message}`);
      }
      throw new Error(`Failed to delete ${resource} with id ${params.id}: ${error.message}`);
    }
  },

  //Delete multiple resources by their IDs
  deleteMany: async (resource, params) => {
    try {
      const promises = params.ids.map((id) =>
        fetchJson(`${API_URL}/${resource}/${id}`, {
          method: 'DELETE',
        })
      );
      await Promise.all(promises);
      return { data: params.ids };
    } catch (error) {
      throw new Error(`Failed to delete multiple ${resource}: ${error.message}`);
    }
  },
};

