import React from "react";
import Link from 'next/link';

export default function NotFound() {
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
      <h1 style={{ fontSize: '3rem', color: '#1976d2', marginBottom: '1rem' }}>404</h1>
      <h2 style={{ marginBottom: '1rem' }}>Page Not Found</h2>
      <p style={{ color: '#666', marginBottom: '2rem' }}>
        The page you are looking for might have been removed or is temporarily unavailable.
      </p>
      <Link href="/" style={{
        backgroundColor: '#1976d2',
        color: 'white',
        padding: '10px 20px',
        borderRadius: '4px',
        textDecoration: 'none',
        fontWeight: 'bold'
      }}>
        Return Home
      </Link>
    </div>
  );
}
