'use client';

import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import api, { BACKEND_URL } from '@/services/api';

interface User {
  id: number;
  email: string;
  name: string;
  role: string;
  status: string;
  business_id?: number;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (tokenOrResponse: string | { access_token: string; refresh_token?: string }) => void;
  logout: () => void;
  signInWithGoogle: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [mounted, setMounted] = useState(false);
  const router = useRouter();
  const pathname = usePathname();

  const fetchUser = async (retryCount = 0, maxRetries = 3) => {
    try {
      const response = await api.get('/auth/me');
      setUser(response.data);
    } catch (error: any) {
      // Network errors or timeout - retry
      const isNetworkError = error.code === 'ECONNABORTED' || 
                             error.message === 'Network Error' ||
                             !error.response;
      
      if (isNetworkError && retryCount < maxRetries) {
        console.log(`Retrying fetchUser (${retryCount + 1}/${maxRetries})...`);
        // Wait before retrying (exponential backoff)
        await new Promise(resolve => setTimeout(resolve, 1000 * (retryCount + 1)));
        return fetchUser(retryCount + 1, maxRetries);
      }
      
      // Only clear token on actual auth errors (401/403), not network errors
      if (error.response?.status === 401 || error.response?.status === 403) {
        console.error('Failed to fetch user: Unauthorized');
        localStorage.removeItem('token');
        setUser(null);
      } else {
        // Network error - keep user logged in, just don't set user data
        console.error('Failed to fetch user (network issue):', error.message);
        // Don't clear the token - the user is still logged in, backend might be cold
      }
    } finally {
      setIsLoading(false);
    }
  };

  // Keepalive ping to prevent backend cold starts (Render free tier spins down after 15 min)
  const pingBackend = useCallback(() => {
    fetch(`${BACKEND_URL}/health`, { method: 'GET', mode: 'no-cors' }).catch(() => {
      // Silently ignore errors - this is just a keepalive ping
    });
  }, []);

  // Set mounted state after hydration
  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    // Only run after component is mounted (client-side)
    if (!mounted) return;
    
    const token = localStorage.getItem('token');
    if (token) {
      fetchUser();
    } else {
      setIsLoading(false);
    }
  }, [mounted]);

  // Set up keepalive ping every 4 minutes when user is authenticated
  useEffect(() => {
    if (!user) return;

    // Ping immediately when user logs in
    pingBackend();

    // Then ping every 4 minutes (well under Render's 15-min cold start threshold)
    const interval = setInterval(pingBackend, 4 * 60 * 1000);

    return () => clearInterval(interval);
  }, [user, pingBackend]);

  const login = async (tokenOrResponse: string | { access_token: string; refresh_token?: string }) => {
    if (typeof tokenOrResponse === 'string') {
      // Firebase token (string) - backward compat
      localStorage.setItem('token', tokenOrResponse);
    } else {
      // JWT response object with access + refresh tokens
      localStorage.setItem('token', tokenOrResponse.access_token);
      if (tokenOrResponse.refresh_token) {
        localStorage.setItem('refreshToken', tokenOrResponse.refresh_token);
      }
    }
    // Wait for user fetch to complete before redirecting
    await fetchUser();
    router.push('/');
  };

  const signInWithGoogle = async () => {
    try {
      // Initialize Firebase Auth (dynamically import to avoid SSR issues)
      const { getAuth, signInWithPopup, GoogleAuthProvider } = await import('firebase/auth');
      const { initializeApp, getApps } = await import('firebase/app');

      // Firebase config from environment variables
      const firebaseConfig = {
        apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
        authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
        projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
        storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET,
        messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
        appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID,
      };

      // Initialize Firebase only once
      if (!getApps().length) {
        initializeApp(firebaseConfig);
      }

      const auth = getAuth();
      const provider = new GoogleAuthProvider();
      
      const result = await signInWithPopup(auth, provider);
      const token = await result.user.getIdToken();
      
      await login(token);
    } catch (error: any) {
      console.error('Google sign-in error:', error);
      throw error;
    }
  };

  const logout = async () => {
    try {
      await api.post('/auth/logout');
    } catch {
      // Ignore errors - we're logging out anyway
    }
    localStorage.removeItem('token');
    localStorage.removeItem('refreshToken');
    setUser(null);
    router.push('/login');
  };

  return (
    <AuthContext.Provider value={{ user, isAuthenticated: !!user, isLoading, login, logout, signInWithGoogle }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
