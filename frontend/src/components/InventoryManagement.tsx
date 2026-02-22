'use client';

import { useState, useEffect } from 'react';
import { useBusiness } from '@/context/BusinessContext';

interface MenuItem {
  id: number;
  name: string;
  inventory: number;
}

const InventoryManagement = () => {
  const { business } = useBusiness();
  const [menuItems, setMenuItems] = useState<MenuItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (business) {
      // Fetch menu items (room types)
      // This is a placeholder, needs actual API call
      const fetchMenuItems = async () => {
        setLoading(true);
        // Replace with your actual API endpoint for fetching menu items
        // For now, we'll use mock data.
        const mockData: MenuItem[] = [
          { id: 1, name: 'King Bed Room', inventory: 10 },
          { id: 2, name: 'Queen Bed Room', inventory: 20 },
          { id: 3, name: 'Suite', inventory: 5 },
        ];
        setMenuItems(mockData);
        setLoading(false);
      };
      fetchMenuItems();
    }
  }, [business]);

  const handleInventoryChange = (itemId: number, newInventory: number) => {
    // API call to update inventory
    console.log(`Updating item ${itemId} to inventory ${newInventory}`);
    // Update local state optimisticly
    setMenuItems(prevItems =>
      prevItems.map(item =>
        item.id === itemId ? { ...item, inventory: newInventory } : item
      )
    );
  };

  if (loading) {
    return <div>Loading inventory...</div>;
  }

  if (!business || menuItems.length === 0) {
    return <div>No inventory items found for this business.</div>;
  }

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold">Inventory Management</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {menuItems.map(item => (
          <div key={item.id} className="p-4 border rounded-lg shadow-sm">
            <h3 className="text-lg font-semibold">{item.name}</h3>
            <div className="mt-2 flex items-center space-x-2">
              <label htmlFor={`inventory-${item.id}`} className="text-sm">Quantity:</label>
              <input
                type="number"
                id={`inventory-${item.id}`}
                value={item.inventory}
                onChange={(e) => handleInventoryChange(item.id, parseInt(e.target.value, 10))}
                className="w-24 p-2 border rounded-md"
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default InventoryManagement;
