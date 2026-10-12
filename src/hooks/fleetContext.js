import { createContext, useContext } from 'react';

export const FleetContext = createContext(null);

export function useFleetState() {
  return useContext(FleetContext);
}
