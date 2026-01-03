import React from 'react';
import { Admin, Resource } from 'react-admin';
import { authProvider } from './authProvider';
import { dataProvider } from './dataProvider';
import { UserList, UserCreate, UserEdit, UserShow } from './users';
import LoginPage from './LoginPage';

const App = () => (
  <Admin
    authProvider={authProvider}
    dataProvider={dataProvider}
    loginPage={LoginPage}
  >
    <Resource name="users" list={UserList} create={UserCreate} edit={UserEdit} show={UserShow} />
  </Admin>
);

export default App;

