import { useState, useCallback } from 'react';
import { FleetContext } from './fleetContext';

/**
 * Minimal in-memory app state for the Batch 1 shell.
 *
 * This is intentionally small and mock-only: it backs the customer portal's
 * "book a shipment" flow and the topbar notification list so the shell is
 * navigable. It is replaced by a real typed API client + server state in
 * later batches (see .kiro/steering/structure.md).
 *
 * The `useFleetState` hook lives in ./fleetContext so this file only exports a
 * component (keeps react-refresh happy).
 */
let nextNotifId = 1;

export function FleetProvider({ children }) {
  const [notifications, setNotifications] = useState([]);
  const [userShipments, setUserShipments] = useState([]);

  const pushNotification = useCallback(({ type, title, message }) => {
    setNotifications(prev => [
      { id: nextNotifId++, type, title, message, time: 'Just now', read: false },
      ...prev,
    ]);
  }, []);

  const markAllRead = useCallback(() => {
    setNotifications(prev => prev.map(n => ({ ...n, read: true })));
  }, []);

  const dismissNotification = useCallback((id) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  }, []);

  const clearAllNotifications = useCallback(() => setNotifications([]), []);

  // Customer books a shipment — creates a local, pending shipment record.
  const bookShipment = useCallback((form) => {
    const shipId = `SHP-${Math.floor(1000 + Math.random() * 9000)}`;
    const origin = form.pickupCity && form.pickupState
      ? `${form.pickupCity}, ${form.pickupState}`
      : form.pickup || 'TBD';
    const dest = form.destCity && form.destState
      ? `${form.destCity}, ${form.destState}`
      : form.dest || 'TBD';
    const now = new Date().toLocaleString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });

    const shipment = {
      id: shipId,
      origin,
      dest,
      status: 'Pending',
      commodity: form.commodity || 'General Freight',
      weight: `${parseInt(form.weight || 0, 10).toLocaleString()} lbs`,
      trailer: form.trailer || 'Dry Van',
      pickupDate: form.pickupDate || now,
      company: form.company || '',
      events: [
        { label: 'Booking request received', time: now, done: true },
        { label: 'Awaiting confirmation', time: 'Pending', done: false },
        { label: 'Pickup scheduled', time: 'Pending', done: false },
        { label: 'Delivered', time: 'Pending', done: false },
      ],
    };

    setUserShipments(prev => [shipment, ...prev]);
    pushNotification({
      type: 'info',
      title: `Shipment booked — ${shipId}`,
      message: `${origin} → ${dest} · ${shipment.commodity}`,
    });
    return shipId;
  }, [pushNotification]);

  return (
    <FleetContext.Provider value={{
      notifications, pushNotification, markAllRead, dismissNotification, clearAllNotifications,
      userShipments, bookShipment,
    }}>
      {children}
    </FleetContext.Provider>
  );
}
