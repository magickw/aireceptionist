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
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (token: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
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

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      fetchUser();
    } else {
      setIsLoading(false);
    }
  }, []);

  // Set up keepalive ping every 4 minutes when user is authenticated
  useEffect(() => {
    if (!user) return;

    // Ping immediately when user logs in
    pingBackend();

    // Then ping every 4 minutes (well under Render's 15-min cold start threshold)
    const interval = setInterval(pingBackend, 4 * 60 * 1000);

    return () => clearInterval(interval);
  }, [user, pingBackend]);

  const login = async (token: string) => {
    localStorage.setItem('token', token);
    // Wait for user fetch to complete before redirecting
    await fetchUser();
    router.push('/');
  };

  const logout = () => {
    localStorage.removeItem('token');
    setUser(null);
    router.push('/login');
  };

  return (
    <AuthContext.Provider value={{ user, isAuthenticated: !!user, isLoading, login, logout }}>
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
