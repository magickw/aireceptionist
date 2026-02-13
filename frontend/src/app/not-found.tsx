import React from "react";
import Link from 'next/link';

export default function NotFound() {
  return (
    <html>
      <head>
        <title>404 - Page Not Found</title>
      </head>
      <body style={{ 
        display: 'flex', 
        flexDirection: 'column', 
        alignItems: 'center', 
        justifyContent: 'center', 
        minHeight: '100vh',
        margin: 0,
        fontFamily: 'sans-serif'
      }}>
        <h1 style={{ fontSize: '3rem', color: '#1e3a8a' }}>404</h1>
        <h2>Page Not Found</h2>
        <Link href="/">Return Home</Link>
      </body>
    </html>
  );
}
