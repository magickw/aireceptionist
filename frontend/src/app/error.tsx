'use client';

import { useEffect } from 'react';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div style={{ 
      display: 'flex', 
      flexDirection: 'column', 
      alignItems: 'center', 
      justifyContent: 'center', 
      minHeight: '60vh',
      textAlign: 'center',
      fontFamily: 'sans-serif'
    }}>
      <h1 style={{ fontSize: '2rem', color: '#ef4444', marginBottom: '1rem' }}>Something went wrong!</h1>
      <p style={{ color: '#666', marginBottom: '2rem' }}>
        We apologize for the inconvenience. An unexpected error has occurred.
      </p>
      <button
        onClick={() => reset()}
        style={{
          backgroundColor: '#1e3a8a',
          color: 'white',
          padding: '10px 20px',
          borderRadius: '4px',
          border: 'none',
          cursor: 'pointer',
          fontWeight: 'bold'
        }}
      >
        Try again
      </button>
    </div>
  );
}
