'use client';

import React from 'react';

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html lang="en">
      <body style={{ 
        display: 'flex', 
        flexDirection: 'column', 
        alignItems: 'center', 
        justifyContent: 'center', 
        minHeight: '100vh',
        margin: 0,
        fontFamily: 'sans-serif'
      }}>
        <h1 style={{ color: '#ef4444' }}>A Critical Error Occurred</h1>
        <button onClick={() => reset()}>Try again</button>
      </body>
    </html>
  );
}
