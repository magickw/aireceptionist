"use client";

import React, { useState, useEffect } from 'react';
import { Container, Typography, Box, Paper, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Chip, IconButton } from '@mui/material';
import { AccessTime, AttachMoney, Person, Phone, ShoppingCart, Event } from '@mui/icons-material';
import api from '@/services/api';
import { format } from 'date-fns';
import Header from '@/components/Header';

interface OrderItem {
  id: number;
  item_name: string;
  quantity: number;
  unit_price: number;
  notes?: string;
}

interface Order {
  id: number;
  customer_name: string;
  customer_phone: string;
  total_amount: number;
  status: string;
  created_at: string;
  items: OrderItem[];
  call_session_id?: string;
}

const OrdersPage: React.FC = () => {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchOrders = async () => {
      try {
        setLoading(true);
        const response = await api.get('/orders/');
        setOrders(response.data);
      } catch (err) {
        console.error("Failed to fetch orders:", err);
        setError("Failed to load orders. Please try again later.");
      } finally {
        setLoading(false);
      }
    };

    fetchOrders();
  }, []);

  const getStatusChipColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'pending': return 'default';
      case 'confirmed': return 'primary';
      case 'preparing': return 'info';
      case 'ready': return 'warning';
      case 'completed': return 'success';
      case 'cancelled': return 'error';
      default: return 'default';
    }
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Header title="Order Management" />
      <Box sx={{ my: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Customer Orders
        </Typography>
        <Typography variant="body1" color="text.secondary" paragraph>
          Track and manage all customer orders placed through the AI agent.
        </Typography>

        {loading && <Typography>Loading orders...</Typography>}
        {error && <Typography color="error">{error}</Typography>}

        {!loading && !error && orders.length === 0 && (
          <Typography>No orders found for your business.</Typography>
        )}

        {!loading && !error && orders.length > 0 && (
          <TableContainer component={Paper} elevation={3}>
            <Table aria-label="orders table">
              <TableHead>
                <TableRow>
                  <TableCell><ShoppingCart /> Order ID</TableCell>
                  <TableCell><Person /> Customer</TableCell>
                  <TableCell><Phone /> Phone</TableCell>
                  <TableCell>Items</TableCell>
                  <TableCell><AttachMoney /> Total</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell><Event /> Placed At</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {orders.map((order) => (
                  <TableRow key={order.id}>
                    <TableCell>{order.id}</TableCell>
                    <TableCell>{order.customer_name}</TableCell>
                    <TableCell>{order.customer_phone}</TableCell>
                    <TableCell>
                      {order.items.map((item, index) => (
                        <Typography key={index} variant="body2">
                          {item.quantity}x {item.item_name} (${item.unit_price.toFixed(2)} each)
                        </Typography>
                      ))}
                    </TableCell>
                    <TableCell>${order.total_amount.toFixed(2)}</TableCell>
                    <TableCell>
                      <Chip label={order.status} color={getStatusChipColor(order.status)} size="small" />
                    </TableCell>
                    <TableCell>{format(new Date(order.created_at), 'MMM d, yyyy h:mm a')}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Box>
    </Container>
  );
};

export default OrdersPage;
