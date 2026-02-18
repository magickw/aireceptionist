"use client";

import React, { useState, useEffect, useCallback } from 'react';
import {
  Container, Typography, Box, Paper, Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow, Chip, IconButton, Dialog,
  DialogTitle, DialogContent, DialogActions, Button, Divider,
  Alert, CircularProgress, Tooltip
} from '@mui/material';
import { AccessTime, AttachMoney, Person, Phone, ShoppingCart, Event, Payment } from '@mui/icons-material';
import api from '@/services/api';
import { format } from 'date-fns';

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

  // Payment dialog state
  const [paymentDialogOpen, setPaymentDialogOpen] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
  const [stripeConfigured, setStripeConfigured] = useState<boolean | null>(null);
  const [paymentStatusLoading, setPaymentStatusLoading] = useState(false);
  const [checkoutLoading, setCheckoutLoading] = useState(false);
  const [markPaidLoading, setMarkPaidLoading] = useState(false);
  const [paymentError, setPaymentError] = useState<string | null>(null);
  const [paymentSuccess, setPaymentSuccess] = useState<string | null>(null);

  const fetchOrders = useCallback(async () => {
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
  }, []);

  useEffect(() => {
    fetchOrders();
  }, [fetchOrders]);

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

  const handleOpenPaymentDialog = async (order: Order) => {
    setSelectedOrder(order);
    setPaymentDialogOpen(true);
    setPaymentError(null);
    setPaymentSuccess(null);
    setStripeConfigured(null);

    // Check Stripe payment status
    setPaymentStatusLoading(true);
    try {
      const response = await api.get('/payments/status');
      setStripeConfigured(response.data?.configured ?? false);
    } catch (err) {
      console.error("Failed to check payment status:", err);
      setStripeConfigured(false);
    } finally {
      setPaymentStatusLoading(false);
    }
  };

  const handleClosePaymentDialog = () => {
    setPaymentDialogOpen(false);
    setSelectedOrder(null);
    setPaymentError(null);
    setPaymentSuccess(null);
    setStripeConfigured(null);
  };

  const handleCreateCheckout = async () => {
    if (!selectedOrder) return;
    setCheckoutLoading(true);
    setPaymentError(null);
    try {
      const response = await api.post('/payments/checkout', {
        order_id: selectedOrder.id,
        success_url: window.location.href,
        cancel_url: window.location.href,
      });
      const checkoutUrl = response.data?.url || response.data?.checkout_url;
      if (checkoutUrl) {
        window.open(checkoutUrl, '_blank');
      } else {
        setPaymentError("No checkout URL returned from the server.");
      }
    } catch (err: any) {
      console.error("Failed to create checkout session:", err);
      const message = err.response?.data?.detail || err.message || "Failed to create checkout session.";
      setPaymentError(message);
    } finally {
      setCheckoutLoading(false);
    }
  };

  const handleMarkAsPaid = async () => {
    if (!selectedOrder) return;
    setMarkPaidLoading(true);
    setPaymentError(null);
    try {
      await api.put(`/orders/${selectedOrder.id}`, { status: 'completed' });
      setPaymentSuccess("Order has been marked as paid and completed.");
      // Update the order in the local state
      setOrders((prev) =>
        prev.map((o) =>
          o.id === selectedOrder.id ? { ...o, status: 'completed' } : o
        )
      );
      setSelectedOrder((prev) => prev ? { ...prev, status: 'completed' } : null);
    } catch (err: any) {
      console.error("Failed to mark order as paid:", err);
      const message = err.response?.data?.detail || err.message || "Failed to update order status.";
      setPaymentError(message);
    } finally {
      setMarkPaidLoading(false);
    }
  };

  const isPaymentEligible = (status: string) => {
    const lower = status.toLowerCase();
    return lower === 'confirmed' || lower === 'pending';
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
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
                  <TableCell><Payment /> Payment</TableCell>
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
                    <TableCell>
                      {isPaymentEligible(order.status) ? (
                        <Tooltip title="Collect Payment">
                          <IconButton
                            color="primary"
                            onClick={() => handleOpenPaymentDialog(order)}
                            size="small"
                          >
                            <Payment />
                          </IconButton>
                        </Tooltip>
                      ) : (
                        <Typography variant="body2" color="text.disabled">
                          --
                        </Typography>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Box>

      {/* Payment Dialog */}
      <Dialog
        open={paymentDialogOpen}
        onClose={handleClosePaymentDialog}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Payment color="primary" />
          Collect Payment
        </DialogTitle>
        <DialogContent>
          {selectedOrder && (
            <>
              {/* Order Summary */}
              <Typography variant="subtitle1" fontWeight="bold" sx={{ mt: 1, mb: 1 }}>
                Order #{selectedOrder.id} - {selectedOrder.customer_name}
              </Typography>
              <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
                {selectedOrder.items.map((item, index) => (
                  <Box
                    key={index}
                    sx={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      mb: index < selectedOrder.items.length - 1 ? 1 : 0,
                    }}
                  >
                    <Typography variant="body2">
                      {item.quantity}x {item.item_name}
                      {item.notes ? ` (${item.notes})` : ''}
                    </Typography>
                    <Typography variant="body2" fontWeight="medium">
                      ${(item.quantity * item.unit_price).toFixed(2)}
                    </Typography>
                  </Box>
                ))}
                <Divider sx={{ my: 1 }} />
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="subtitle2" fontWeight="bold">
                    Total
                  </Typography>
                  <Typography variant="subtitle2" fontWeight="bold">
                    ${selectedOrder.total_amount.toFixed(2)}
                  </Typography>
                </Box>
              </Paper>

              <Divider sx={{ mb: 2 }} />

              {/* Payment Status Messages */}
              {paymentError && (
                <Alert severity="error" sx={{ mb: 2 }}>
                  {paymentError}
                </Alert>
              )}
              {paymentSuccess && (
                <Alert severity="success" sx={{ mb: 2 }}>
                  {paymentSuccess}
                </Alert>
              )}

              {/* Payment Status Loading */}
              {paymentStatusLoading && (
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                  <CircularProgress size={20} />
                  <Typography variant="body2" color="text.secondary">
                    Checking payment configuration...
                  </Typography>
                </Box>
              )}

              {/* Stripe Not Configured Warning */}
              {!paymentStatusLoading && stripeConfigured === false && (
                <Alert severity="info" sx={{ mb: 2 }}>
                  Stripe is not configured. Set STRIPE_SECRET_KEY in environment variables.
                </Alert>
              )}

              {/* Stripe Checkout Button */}
              {!paymentStatusLoading && stripeConfigured === true && !paymentSuccess && (
                <Button
                  variant="contained"
                  color="primary"
                  onClick={handleCreateCheckout}
                  disabled={checkoutLoading}
                  startIcon={checkoutLoading ? <CircularProgress size={18} /> : <Payment />}
                  fullWidth
                  sx={{ mb: 2 }}
                >
                  {checkoutLoading ? 'Creating Checkout...' : 'Create Checkout'}
                </Button>
              )}

              {/* Manual Mark as Paid */}
              {!paymentSuccess && (
                <Button
                  variant="outlined"
                  color="success"
                  onClick={handleMarkAsPaid}
                  disabled={markPaidLoading}
                  startIcon={markPaidLoading ? <CircularProgress size={18} /> : <AttachMoney />}
                  fullWidth
                >
                  {markPaidLoading ? 'Updating...' : 'Mark as Paid'}
                </Button>
              )}
            </>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClosePaymentDialog}>
            {paymentSuccess ? 'Done' : 'Cancel'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default OrdersPage;
