import React, { useState } from 'react';
import {
  List,
  Datagrid,
  TextField,
  EmailField,
  Edit,
  Create,
  Show,
  SimpleShowLayout,
  SimpleForm,
  TextInput,
  SelectInput,
  required,
  email,
  minLength,
  maxLength,
  Filter,
  SearchInput,
  EditButton,
  DeleteButton,
  ShowButton,
  usePermissions,
  TopToolbar,
  CreateButton,
  useNotify,
  useRedirect,
  DateField,
  useGetIdentity,
  Button,
  useListContext,
} from 'react-admin';
import { usersAPI } from '../api/apiService';

// Validation functions with strict rules
const validateName = [
  required('Name is required'),
  minLength(2, 'Name must be at least 2 characters'),
  maxLength(100, 'Name must not exceed 100 characters'),
  (value) => {
    if (value && !/^[a-zA-Z0-9\s\-_\.]+$/.test(value.trim())) {
      return 'Name contains invalid characters';
    }
    return undefined;
  }
];

const validateEmail = [
  required('Email is required'),
  email('Invalid email format'),
  (value) => {
    if (value) {
      const trimmed = value.trim().toLowerCase();
      if (trimmed.length > 100) {
        return 'Email address is too long';
      }
      // Additional email format check
      const emailPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
      if (!emailPattern.test(trimmed)) {
        return 'Invalid email format';
      }
    }
    return undefined;
  }
];

const validatePassword = [
  required('Password is required'),
  minLength(1, 'Password cannot be empty'),
  maxLength(100, 'Password is too long'),
  (value) => {
    if (value && value.trim() !== value) {
      return 'Password cannot have leading or trailing whitespace';
    }
    return undefined;
  }
];

// Custom validator for optional password (allows empty, validates length if provided)
const validatePasswordOptional = (value) => {
  if (!value || value.trim() === '') {
    return undefined; // Empty is allowed
  }
  if (value.length < 1) {
    return 'Password must be at least 1 character';
  }
  return undefined;
};

// Format functions for display
const formatRole = (value) => {
  if (!value) return 'N/A';
  return value.charAt(0).toUpperCase() + value.slice(1);
};

const formatStatus = (value) => {
  if (!value) return 'N/A';
  return value.charAt(0).toUpperCase() + value.slice(1);
};

const formatAccountRole = (value) => {
  if (!value) return 'N/A';
  return value
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
};

// Filter component for User List
const UserFilter = (props) => (
  <Filter {...props}>
    <SearchInput source="search" placeholder="Search name or email" alwaysOn />
    <SelectInput
      source="role"
      choices={[
        { id: 'manager', name: 'Manager' },
        { id: 'developer', name: 'Developer' },
      ]}
      alwaysOn={false}
    />
    <SelectInput
      source="status"
      choices={[
        { id: 'active', name: 'Active' },
        { id: 'inactive', name: 'Inactive' },
      ]}
      alwaysOn={false}
    />
    <SelectInput
      source="account_role"
      choices={[
        { id: 'admin', name: 'Admin' },
        { id: 'corporate_admin', name: 'Corporate Admin' },
        { id: 'end_user', name: 'End User' },
      ]}
      alwaysOn={false}
    />
  </Filter>
);

// Bulk Upload Component - Simple modal implementation
const BulkUploadButton = () => {
  const { permissions } = usePermissions();
  const [open, setOpen] = useState(false);
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [results, setResults] = useState(null);
  const notify = useNotify();

  if (!permissions?.canCreate) {
    return null; // Only admin can see this
  }

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      if (!selectedFile.name.endsWith('.csv')) {
        notify('Please select a CSV file', { type: 'error' });
        return;
      }
      setFile(selectedFile);
      setResults(null);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      notify('Please select a CSV file', { type: 'error' });
      return;
    }

    setUploading(true);
    try {
      const data = await usersAPI.uploadCSV(file);
      console.log('Upload response:', data);

      setResults(data);
      notify(`Upload complete: ${data.users_created} users created`, { 
        type: data.errors.length > 0 ? 'warning' : 'success' 
      });
    } catch (error) {
      notify(error.message || 'Upload failed', { type: 'error' });
      setResults(null);
    } finally {
      setUploading(false);
    }
  };

  const handleClose = () => {
    setOpen(false);
    setFile(null);
    setResults(null);
  };

  // Simple modal styles
  const modalStyle = {
    display: open ? 'block' : 'none',
    position: 'fixed',
    zIndex: 1300,
    left: 0,
    top: 0,
    width: '100%',
    height: '100%',
    overflow: 'auto',
    backgroundColor: 'rgba(0,0,0,0.4)',
  };

  const modalContentStyle = {
    backgroundColor: '#fefefe',
    margin: '5% auto',
    padding: '20px',
    border: '1px solid #888',
    width: '80%',
    maxWidth: '600px',
    borderRadius: '4px',
  };

  const buttonStyle = {
    margin: '5px',
    padding: '8px 16px',
    cursor: 'pointer',
    border: '1px solid #ccc',
    borderRadius: '4px',
    backgroundColor: '#fff',
  };

  return (
    <>
      <Button
        label="Bulk Upload"
        onClick={() => setOpen(true)}
      />
      {open && (
        <div style={modalStyle} onClick={handleClose}>
          <div style={modalContentStyle} onClick={(e) => e.stopPropagation()}>
            <h2>Bulk Upload Users (CSV)</h2>
            <div style={{ marginBottom: '20px' }}>
              <input
                type="file"
                accept=".csv"
                onChange={handleFileChange}
                disabled={uploading}
                style={{ marginBottom: '10px', display: 'block' }}
              />
              {file && (
                <div style={{ marginTop: '10px', color: '#666' }}>
                  Selected: {file.name}
                </div>
              )}
            </div>

            {results && (
              <div style={{ marginTop: '20px', padding: '15px', backgroundColor: '#f5f5f5', borderRadius: '4px' }}>
                <h3 style={{ marginTop: 0 }}>Upload Results</h3>
                <p>
                  <strong>Total Rows:</strong> {results.total_rows}
                </p>
                <p>
                  <strong>Users Created:</strong> {results.users_created}
                </p>
                {results.errors && results.errors.length > 0 && (
                  <div style={{ marginTop: '15px' }}>
                    <strong>Errors:</strong>
                    <ul style={{ marginTop: '10px', paddingLeft: '20px' }}>
                      {results.errors.map((error, index) => (
                        <li key={index} style={{ marginBottom: '5px' }}>
                          <strong>Row {error.row}:</strong> {error.errors.join(', ')}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}

            <div style={{ marginTop: '20px', textAlign: 'right' }}>
              <button
                style={buttonStyle}
                onClick={handleClose}
                disabled={uploading}
              >
                Cancel
              </button>
              <button
                style={{ ...buttonStyle, backgroundColor: '#1976d2', color: '#fff', border: 'none' }}
                onClick={handleUpload}
                disabled={!file || uploading}
              >
                {uploading ? 'Uploading...' : 'Upload'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

// Custom Export Button - Admin only, uses current filters
const CustomExportButton = () => {
  const { permissions } = usePermissions();
  // Get filterValues and sort from List context
  const { filterValues = {}, sort = {} } = useListContext();
  const [exporting, setExporting] = useState(false);
  const notify = useNotify();

  if (!permissions?.canDelete) {
    return null; // Only admin can export
  }

  const handleExport = async () => {
    setExporting(true);
    try {
      // Use centralized API service
      const blob = await usersAPI.exportCSV(filterValues, sort);
      
      // Trigger download
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = 'users_export.csv';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);

      notify('Export completed successfully', { type: 'success' });
    } catch (error) {
      console.error('Export error:', error);
      notify(error.message || 'Export failed', { type: 'error' });
    } finally {
      setExporting(false);
    }
  };

  return (
    <Button
      label={exporting ? 'Exporting...' : 'Export'}
      onClick={handleExport}
      disabled={exporting}
    />
  );
};

// List Actions Component - conditionally show Create button
const ListActions = (props) => {
  const { permissions } = usePermissions();
  return (
    <TopToolbar {...props}>
      {permissions?.canCreate && <CreateButton />}
      <BulkUploadButton />
      <CustomExportButton />
    </TopToolbar>
  );
};

// Edit Actions Component - conditionally show Delete button
const EditActions = (props) => {
  const { permissions } = usePermissions();
  return (
    <TopToolbar {...props}>
      <ShowButton />
      {permissions?.canDelete && <DeleteButton />}
    </TopToolbar>
  );
};

// User List Component
export const UserList = (props) => {
  const { permissions } = usePermissions();

  return (
    <List
      {...props}
      filters={<UserFilter />}
      actions={<ListActions />}
      perPage={10}
      sort={{ field: 'created_at', order: 'DESC' }}
    >
      <Datagrid
        rowClick="show"
        bulkActionButtons={permissions?.canDelete ? undefined : false}
      >
        <TextField source="name" sortable />
        <EmailField source="email" sortable />
        <TextField
          source="role"
          sortable
          label="Job Role"
          format={formatRole}
        />
        <TextField
          source="status"
          sortable
          format={formatStatus}
        />
        <TextField
          source="account_role"
          sortable
          label="Account Role"
          format={formatAccountRole}
        />
        <DateField source="created_at" sortable showTime />
        <EditButton />
        {permissions?.canDelete && <DeleteButton />}
      </Datagrid>
    </List>
  );
};

// User Create Component - Admin only
export const UserCreate = (props) => {
  const { permissions } = usePermissions();
  const notify = useNotify();
  const redirect = useRedirect();

  // Check if user has permission to create
  React.useEffect(() => {
    if (permissions && !permissions.canCreate) {
      notify('You do not have permission to create users', { type: 'error' });
      redirect('/users');
    }
  }, [permissions, notify, redirect]);

  if (permissions && !permissions.canCreate) {
    return null;
  }

  return (
    <Create {...props} title="Create User">
      <SimpleForm
        onSubmit={(data) => {
          // Additional client-side validation before submission
          const errors = {};
          
          // Validate name
          if (!data.name || data.name.trim().length < 2) {
            errors.name = 'Name must be at least 2 characters';
          }
          if (data.name && data.name.trim().length > 100) {
            errors.name = 'Name must not exceed 100 characters';
          }
          
          // Validate email
          if (!data.email || !data.email.trim()) {
            errors.email = 'Email is required';
          } else {
            const emailPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
            if (!emailPattern.test(data.email.trim().toLowerCase())) {
              errors.email = 'Invalid email format';
            }
          }
          
          // Validate password
          if (!data.password || data.password.trim().length < 1) {
            errors.password = 'Password is required';
          }
          
          if (Object.keys(errors).length > 0) {
            throw errors;
          }
          
          // Normalize data before submission
          return {
            ...data,
            name: data.name.trim(),
            email: data.email.trim().toLowerCase(),
            password: data.password.trim()
          };
        }}
      >
        <TextInput
          source="name"
          validate={validateName}
          fullWidth
          helperText="User name (2-100 characters, alphanumeric and spaces only)"
        />
        <TextInput
          source="email"
          type="email"
          validate={validateEmail}
          fullWidth
          helperText="Unique email address (will be converted to lowercase)"
        />
        <TextInput
          source="password"
          type="password"
          validate={validatePassword}
          fullWidth
          helperText="User password (1-500 characters, no leading/trailing spaces)"
        />
        <SelectInput
          source="role"
          choices={[
            { id: 'manager', name: 'Manager' },
            { id: 'developer', name: 'Developer' },
          ]}
          fullWidth
          helperText="Job role"
        />
        <SelectInput
          source="status"
          choices={[
            { id: 'active', name: 'Active' },
            { id: 'inactive', name: 'Inactive' },
          ]}
          defaultValue="active"
          fullWidth
          helperText="User status"
        />
        <SelectInput
          source="account_role"
          choices={[
            { id: 'admin', name: 'Admin' },
            { id: 'corporate_admin', name: 'Corporate Admin' },
            { id: 'end_user', name: 'End User' },
          ]}
          defaultValue="end_user"
          fullWidth
          helperText="Account role determines user permissions"
        />
      </SimpleForm>
    </Create>
  );
};

// User Edit Component - Role-based field access
export const UserEdit = (props) => {
  const { permissions } = usePermissions();
  const { identity } = useGetIdentity();
  const notify = useNotify();
  const redirect = useRedirect();

  // Check if user has permission to edit
  React.useEffect(() => {
    if (permissions && !permissions.canEdit) {
      notify('You do not have permission to edit users', { type: 'error' });
      redirect('/users');
    }
  }, [permissions, notify, redirect]);

  if (permissions && !permissions.canEdit) {
    return null;
  }

  // Determine user role - use identity if available, fallback to permissions
  const userRole = identity?.role || (permissions?.canDelete ? 'admin' : 'corporate_admin');
  const isAdmin = userRole === 'admin';
  const isCorporateAdmin = userRole === 'corporate_admin';

  return (
    <Edit {...props} title="Edit User" actions={<EditActions />}>
      <SimpleForm>
        {/* Name field - editable only by admin, hidden for corporate admin */}
        {isAdmin ? (
          <TextInput
            source="name"
            validate={validateName}
            fullWidth
            helperText="User name (2-100 characters)"
          />
        ) : null}
        
        {/* Email field - editable only by admin, hidden for corporate admin */}
        {isAdmin ? (
          <TextInput
            source="email"
            type="email"
            validate={validateEmail}
            fullWidth
            helperText="Unique email address"
          />
        ) : null}
        
        {/* Password field - editable only by admin, hidden for corporate admin */}
        {isAdmin ? (
          <TextInput
            source="password"
            type="password"
            validate={validatePasswordOptional}
            fullWidth
            helperText="Leave empty to keep current password"
            format={(value) => value || ''} // Ensure empty string is sent as empty, not undefined
            parse={(value) => (value && value.trim() !== '' ? value : undefined)} // Convert empty strings to undefined so backend ignores it
          />
        ) : null}
        
        {/* Role field - editable by admin and corporate_admin */}
        <SelectInput
          source="role"
          choices={[
            { id: 'manager', name: 'Manager' },
            { id: 'developer', name: 'Developer' },
          ]}
          fullWidth
          disabled={!isAdmin && !isCorporateAdmin}
          helperText={
            isCorporateAdmin
              ? 'Corporate Admin can only edit job role'
              : 'Job role'
          }
        />
        
        {/* Status field - editable only by admin, hidden for corporate admin */}
        {isAdmin ? (
          <SelectInput
            source="status"
            choices={[
              { id: 'active', name: 'Active' },
              { id: 'inactive', name: 'Inactive' },
            ]}
            fullWidth
            helperText="User status"
          />
        ) : null}
        
        {/* Account role field - editable only by admin, hidden for corporate admin */}
        {isAdmin ? (
          <SelectInput
            source="account_role"
            choices={[
              { id: 'admin', name: 'Admin' },
              { id: 'corporate_admin', name: 'Corporate Admin' },
              { id: 'end_user', name: 'End User' },
            ]}
            fullWidth
            helperText="Account role determines user permissions"
          />
        ) : null}
      </SimpleForm>
    </Edit>
  );
};

// User Show Component
export const UserShow = (props) => (
  <Show {...props} title="User Details">
    <SimpleShowLayout>
      <TextField source="id" label="ID" />
      <TextField source="name" />
      <EmailField source="email" />
      <TextField
        source="role"
        label="Job Role"
        format={formatRole}
      />
      <TextField
        source="status"
        format={formatStatus}
      />
      <TextField
        source="account_role"
        label="Account Role"
        format={formatAccountRole}
      />
      <DateField source="created_at" showTime />
      <DateField source="updated_at" showTime />
    </SimpleShowLayout>
  </Show>
);
