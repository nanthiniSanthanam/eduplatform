/**
 * File: frontend/src/contexts/AuthContext.jsx
 * Purpose: Authentication context provider for JWT-based user authentication
 * 
 * This context provides:
 * 1. User authentication state management
 * 2. Login/logout functionality with JWT token handling
 * 3. User registration and profile management
 * 4. Role-based access control functions
 * 5. Email verification status tracking
 * 
 * Modifications for new backend:
 * 1. Updated to work with JWT token authentication
 * 2. Added role-based access control methods
 * 3. Added email verification status checking
 * 4. Enhanced token refresh mechanism
 * 5. Improved error handling for login failures
 * 
 * Backend Connection Points:
 * - POST /api/token/ - Get JWT tokens
 * - POST /api/token/refresh/ - Refresh JWT tokens
 * - POST /api/users/register/ - Register new users
 * - GET /api/users/me/ - Get current user profile
 * - POST /api/users/verify-email/ - Verify user email
 */

import React, { createContext, useState, useEffect, useContext } from 'react';
import { authService } from '../services/api';

// Create context
const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [currentUser, setCurrentUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Load user on mount and set up token refresh
  useEffect(() => {
    const loadUser = async () => {
      if (authService.isAuthenticated()) {
        try {
          // Try to get the current user with the stored token
          const response = await authService.getCurrentUser();
          setCurrentUser(response.data);
          
          // Set up token refresh interval
          // Refresh token before it expires (e.g., every 25 minutes for 30 min tokens)
          const refreshInterval = setInterval(() => {
            authService.refreshToken()
              .catch(err => {
                console.error('Token refresh failed:', err);
                // If refresh fails, log the user out
                authService.logout();
                setCurrentUser(null);
                clearInterval(refreshInterval);
              });
          }, 25 * 60 * 1000); // 25 minutes
          
          // Clean up interval on unmount
          return () => clearInterval(refreshInterval);
        } catch (err) {
          console.error('Error loading user:', err);
          // Token might be invalid or expired, try to refresh it
          try {
            await authService.refreshToken();
            const retryResponse = await authService.getCurrentUser();
            setCurrentUser(retryResponse.data);
          } catch (refreshErr) {
            console.error('Token refresh failed:', refreshErr);
            // If refresh fails too, log the user out
            authService.logout();
          }
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
  const login = async (email, password, rememberMe = false) => {
    try {
      setError(null);
      // Pass remember me flag to determine token storage behavior
      const data = await authService.login({ email, password, rememberMe });
      
      // Get user details
      const userResponse = await authService.getCurrentUser();
      setCurrentUser(userResponse.data);
      
      return true;
    } catch (err) {
      console.error('Login error:', err);
      const errorMessage = err.response?.data?.detail || 'Failed to login';
      setError(errorMessage);
      return false;
    }
  };

  // Register function
  const register = async (userData) => {
    try {
      setError(null);
      await authService.register(userData);
      
      // With the enhanced backend, we don't auto-login after registration
      // because email verification might be required
      return { 
        success: true, 
        message: 'Registration successful! Please check your email to verify your account.' 
      };
    } catch (err) {
      console.error('Registration error:', err);
      
      // Format error messages from the backend response
      let errorMsg = 'Failed to register';
      if (err.response?.data) {
        const errors = err.response.data;
        
        // Check if it's a structured error object
        if (typeof errors === 'object' && !Array.isArray(errors)) {
          const messages = [];
          for (const field in errors) {
            const fieldErrors = errors[field];
            if (Array.isArray(fieldErrors)) {
              messages.push(`${field}: ${fieldErrors.join(', ')}`);
            } else {
              messages.push(`${field}: ${fieldErrors}`);
            }
          }
          errorMsg = messages.join('; ');
        } else if (typeof errors === 'string') {
          errorMsg = errors;
        }
      }
      
      setError(errorMsg);
      return { success: false, error: errorMsg };
    }
  };

  // Logout function
  const logout = () => {
    authService.logout();
    setCurrentUser(null);
  };

  // Verify email function
  const verifyEmail = async (token) => {
    try {
      setError(null);
      await authService.verifyEmail(token);
      
      // If the user is already logged in, update their verification status
      if (currentUser) {
        const updatedUser = { ...currentUser, isEmailVerified: true };
        setCurrentUser(updatedUser);
      }
      
      return { success: true, message: 'Email verified successfully!' };
    } catch (err) {
      console.error('Email verification error:', err);
      const errorMsg = err.response?.data?.detail || 'Failed to verify email';
      setError(errorMsg);
      return { success: false, error: errorMsg };
    }
  };

  // Request password reset
  const requestPasswordReset = async (email) => {
    try {
      setError(null);
      await authService.requestPasswordReset(email);
      return { success: true, message: 'Password reset email sent!' };
    } catch (err) {
      console.error('Password reset request error:', err);
      const errorMsg = err.response?.data?.detail || 'Failed to request password reset';
      setError(errorMsg);
      return { success: false, error: errorMsg };
    }
  };

  // Reset password
  const resetPassword = async (token, newPassword) => {
    try {
      setError(null);
      await authService.resetPassword(token, newPassword);
      return { success: true, message: 'Password reset successful!' };
    } catch (err) {
      console.error('Password reset error:', err);
      const errorMsg = err.response?.data?.detail || 'Failed to reset password';
      setError(errorMsg);
      return { success: false, error: errorMsg };
    }
  };

  // Update user profile
  const updateUserProfile = async (profileData) => {
    try {
      setError(null);
      const response = await authService.updateProfile(profileData);
      setCurrentUser({ ...currentUser, ...response.data });
      return { success: true, message: 'Profile updated successfully!' };
    } catch (err) {
      console.error('Profile update error:', err);
      const errorMsg = err.response?.data?.detail || 'Failed to update profile';
      setError(errorMsg);
      return { success: false, error: errorMsg };
    }
  };

  // Check if user is authenticated
  const isAuthenticated = () => {
    return !!currentUser;
  };

  // Role-based access control helpers
  const hasRole = (role) => {
    return currentUser?.role === role;
  };
  
  const isStudent = () => hasRole('student');
  const isInstructor = () => hasRole('instructor');
  const isAdmin = () => hasRole('admin');
  const isStaff = () => hasRole('staff');

  // Context value
  const value = {
    currentUser,
    loading,
    error,
    login,
    register,
    logout,
    isAuthenticated,
    verifyEmail,
    requestPasswordReset,
    resetPassword,
    updateUserProfile,
    hasRole,
    isStudent,
    isInstructor,
    isAdmin,
    isStaff,
    setError: (msg) => setError(msg), // Allow clearing or setting error from components
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