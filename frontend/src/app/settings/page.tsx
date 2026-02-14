'use client';
import * as React from 'react';
import Container from '@mui/material/Container';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import { useState, useEffect } from 'react';
import axios from 'axios';
import Select from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';
import InputLabel from '@mui/material/InputLabel';
import FormControl from '@mui/material/FormControl';
import RestaurantIcon from '@mui/icons-material/Restaurant';
import ContentCutIcon from '@mui/icons-material/ContentCut';
import SpaIcon from '@mui/icons-material/Spa';
import BusinessIcon from '@mui/icons-material/Business';

export default function SettingsPage() {
  const [businessName, setBusinessName] = useState('');
  const [businessType, setBusinessType] = useState('');
  const [businessId, setBusinessId] = useState(null);
  const [operatingHours, setOperatingHours] = useState<any>({
    0: { open: 9, close: 17 }, // Sunday
    1: { open: 9, close: 17 }, // Monday
    2: { open: 9, close: 17 }, // Tuesday
    3: { open: 9, close: 17 }, // Wednesday
    4: { open: 9, close: 17 }, // Thursday
    5: { open: 9, close: 17 }, // Friday
    6: { open: 9, close: 17 }, // Saturday
  });

  useEffect(() => {
    // In a real application, you would fetch the business ID for the logged-in user.
    // For now, we'll assume a default business ID (e.g., 1) or fetch the first one.
    const fetchBusiness = async () => {
      try {
        const response = await axios.get(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/businesses`);
        if (response.data.length > 0) {
          const business = response.data[0];
          setBusinessId(business.id);
          setBusinessName(business.name);
          setBusinessType(business.type);
          if (business.operating_hours) {
            setOperatingHours(business.operating_hours);
          }
        }
      } catch (error) {
        console.error('Error fetching business:', error);
      }
    };
    fetchBusiness();
  }, []);

  const handleHoursChange = (day: number, type: 'open' | 'close', value: number) => {
    setOperatingHours({
      ...operatingHours,
      [day]: { ...operatingHours[day], [type]: value },
    });
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    try {
      if (businessId) {
        await axios.put(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/businesses/${businessId}`, {
          name: businessName,
          type: businessType,
          settings: {},
          operating_hours: operatingHours,
        });
        alert('Business settings updated successfully!');
      } else {
        const response = await axios.post(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/businesses`, {
          name: businessName,
          type: businessType,
          settings: {},
          operating_hours: operatingHours,
        });
        setBusinessId(response.data.id);
        alert('Business created successfully!');
      }
    } catch (error) {
      console.error('Error saving business settings:', error);
      alert('Failed to save business settings.');
    }
  };

  const businessTypes = [
    { value: 'restaurant', label: 'Restaurant', icon: <RestaurantIcon /> },
    { value: 'salon', label: 'Hair Salon', icon: <ContentCutIcon /> },
    { value: 'spa', label: 'Spa & Wellness', icon: <SpaIcon /> },
    { value: 'medical', label: 'Medical Practice', icon: <BusinessIcon /> },
    { value: 'dental', label: 'Dental Office', icon: <BusinessIcon /> },
    { value: 'fitness', label: 'Fitness Center', icon: <BusinessIcon /> },
    { value: 'automotive', label: 'Auto Service', icon: <BusinessIcon /> },
    { value: 'legal', label: 'Law Firm', icon: <BusinessIcon /> },
    { value: 'accounting', label: 'Accounting', icon: <BusinessIcon /> },
    { value: 'consulting', label: 'Consulting', icon: <BusinessIcon /> },
    { value: 'real-estate', label: 'Real Estate', icon: <BusinessIcon /> },
    { value: 'veterinary', label: 'Veterinary Clinic', icon: <BusinessIcon /> },
    { value: 'retail', label: 'Retail Store', icon: <BusinessIcon /> },
    { value: 'cleaning', label: 'Cleaning Service', icon: <BusinessIcon /> },
    { value: 'education', label: 'Education/Tutoring', icon: <BusinessIcon /> },
    { value: 'photography', label: 'Photography Studio', icon: <BusinessIcon /> },
    { value: 'plumbing', label: 'Plumbing Service', icon: <BusinessIcon /> },
    { value: 'electrical', label: 'Electrical Service', icon: <BusinessIcon /> },
    { value: 'landscaping', label: 'Landscaping', icon: <BusinessIcon /> },
    { value: 'insurance', label: 'Insurance Agency', icon: <BusinessIcon /> },
    { value: 'other', label: 'Other', icon: <BusinessIcon /> },
  ];

  const daysOfWeek = [
    'Sunday',
    'Monday',
    'Tuesday',
    'Wednesday',
    'Thursday',
    'Friday',
    'Saturday',
  ];

  return (
    <Container maxWidth="md">
      <Box sx={{ my: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Business Settings
        </Typography>
        <form onSubmit={handleSubmit}>
          <TextField
            label="Business Name"
            variant="outlined"
            fullWidth
            margin="normal"
            value={businessName}
            onChange={(e) => setBusinessName(e.target.value)}
            required
          />
          <FormControl fullWidth margin="normal" required>
            <InputLabel>Business Type</InputLabel>
            <Select
              value={businessType}
              label="Business Type"
              onChange={(e) => setBusinessType(e.target.value)}
            >
              {businessTypes.map((type) => (
                <MenuItem key={type.value} value={type.value}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    {type.icon}
                    {type.label}
                  </Box>
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <Typography variant="h5" component="h2" sx={{ mt: 4, mb: 2 }}>
            Operating Hours
          </Typography>
          {daysOfWeek.map((dayName, index) => (
            <Box key={index} sx={{ display: 'flex', gap: 2, mb: 2, alignItems: 'center' }}>
              <Typography sx={{ width: 100 }}>{dayName}</Typography>
              <FormControl variant="outlined" sx={{ minWidth: 120 }}>
                <InputLabel>Open</InputLabel>
                <Select
                  value={operatingHours[index]?.open || 0}
                  onChange={(e) => handleHoursChange(index, 'open', e.target.value as number)}
                  label="Open"
                >
                  {[...Array(24).keys()].map((hour) => (
                    <MenuItem key={hour} value={hour}>
                      {`${hour}:00`}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              <FormControl variant="outlined" sx={{ minWidth: 120 }}>
                <InputLabel>Close</InputLabel>
                <Select
                  value={operatingHours[index]?.close || 0}
                  onChange={(e) => handleHoursChange(index, 'close', e.target.value as number)}
                  label="Close"
                >
                  {[...Array(24).keys()].map((hour) => (
                    <MenuItem key={hour} value={hour}>
                      {`${hour}:00`}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Box>
          ))}

          <Button type="submit" variant="contained" color="primary" sx={{ mt: 2 }}>
            Save Settings
          </Button>
        </form>
      </Box>
    </Container>
  );
}
