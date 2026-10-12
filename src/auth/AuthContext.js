import { createContext, useContext } from 'react';

export const AuthContext = createContext(null);

export function useAuth() {
  return useContext(AuthContext);
}

export const STAFF_ROLES = ['admin', 'dispatcher', 'dock'];

export const isStaff = (role) => STAFF_ROLES.includes(role);
