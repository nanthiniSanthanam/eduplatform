import React, { createContext, useState, useEffect, useContext } from 'react';
import { authService } from '../services/api';

// Create context
const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [currentUser, setCurrentUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Load user on mount
  useEffect(() => {
    const loadUser = async () => {
      if (authService.isAuthenticated()) {
        try {
          const response = await authService.getCurrentUser();
          setCurrentUser(response.data);
        } catch (err) {
          console.error('Error loading user:', err);
          // Token might be invalid or expired
          authService.logout();
        } finally {
          setLoading(false);
        }
      } else {
        setLoading(false);
      }
    };

    loadUser();
  }, []);

  // Login function
  const login = async (email, password) => {
    try {
      setError(null);
      const data = await authService.login({ email, password });
      
      // Get user details
      const userResponse = await authService.getCurrentUser();
      setCurrentUser(userResponse.data);
      
      return { success: true };
    } catch (err) {
      console.error('Login error:', err);
      setError(err.response?.data?.detail || 'Failed to login');
      return { success: false, error: err.response?.data?.detail || 'Failed to login' };
    }
  };

  // Register function
  const register = async (userData) => {
    try {
      setError(null);
      await authService.register(userData);
      
      // Login after successful registration
      return await login(userData.email, userData.password);
    } catch (err) {
      console.error('Registration error:', err);
      setError(err.response?.data || 'Failed to register');
      return { success: false, error: err.response?.data || 'Failed to register' };
    }
  };

  // Logout function
  const logout = () => {
    authService.logout();
    setCurrentUser(null);
  };

  // Check if user is authenticated
  const isAuthenticated = () => {
    return !!currentUser;
  };

  // Context value
  const value = {
    currentUser,
    loading,
    error,
    login,
    register,
    logout,
    isAuthenticated
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

// Custom hook for using auth context
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;