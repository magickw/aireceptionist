'use client';
import React from 'react';
import dynamic from 'next/dynamic';
import { TextField } from '@mui/material';
import dayjs, { Dayjs } from 'dayjs';

// Dynamically import date-related components to ensure they are client-side only
const LocalizationProvider = dynamic(() => import('@mui/x-date-pickers/LocalizationProvider').then(mod => mod.LocalizationProvider), { ssr: false });
const AdapterDayjs = dynamic(() => import('@mui/x-date-pickers/AdapterDayjs').then(mod => mod.AdapterDayjs), { ssr: false });
const DateTimePicker = dynamic(() => import('@mui/x-date-pickers/DateTimePicker').then(mod => mod.DateTimePicker), { ssr: false });

interface CalendarDatePickerProps {
  selectedDate: Dayjs;
  handleDateChange: (date: Dayjs | null) => void;
}

const CalendarDatePicker: React.FC<CalendarDatePickerProps> = ({ selectedDate, handleDateChange }) => {
  if (typeof window === 'undefined') {
    // During SSR, return a placeholder or null
    return (
      <TextField
        label="Select Date"
        value={selectedDate.format('YYYY-MM-DD HH:mm')}
        fullWidth
        disabled
      />
    );
  }

  return (
    <LocalizationProvider dateAdapter={AdapterDayjs}>
      <DateTimePicker
        label="Select Date"
        value={selectedDate}
        onChange={handleDateChange}
        renderInput={(params) => <TextField {...params} fullWidth />}
        slotProps={{
          actionBar: {
            actions: ['clear', 'today'],
          },
        }}
      />
    </LocalizationProvider>
  );
};

export default CalendarDatePicker;
