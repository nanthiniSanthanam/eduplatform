/**
 * File: frontend/src/contexts/AuthContext.jsx
 * Purpose: Authentication context provider for JWT-based user authentication with subscription management
 * 
 * This context provides:
 * 1. User authentication state management
 * 2. Login/logout functionality with JWT token handling
 * 3. User registration and profile management
 * 4. Role-based access control functions
 * 5. Email verification status tracking
 * 6. Subscription management for tiered access
 * 7. Access level determination (basic, intermediate, advanced)
 * 
 * Modifications for tiered access:
 * 1. Added subscription state to track user's subscription tier
 * 2. Added getAccessLevel function to determine content access level
 * 3. Added subscription management functions (upgrade, cancel)
 * 4. Added isSubscriber helper function
 * 5. Connected to subscription endpoints in API
 * 
 * Access Levels:
 * - Unregistered users: basic access
 * - Registered users: intermediate access
 * - Paid users: intermediate (basic tier) or advanced (premium tier) access
 * 
 * Usage:
 * const { currentUser, subscription, getAccessLevel, isSubscriber, upgradeSubscription } = useAuth();
 * 
 * Variables to modify:
 * - ACCESS_LEVEL_MAP: Change this if you want to modify how subscription tiers map to access levels
 * 
 * Backend Connection Points:
 * - POST /api/token/ - Get JWT tokens
 * - POST /api/token/refresh/ - Refresh JWT tokens
 * - POST /api/users/register/ - Register new users
 * - GET /api/users/me/ - Get current user profile
 * - POST /api/users/verify-email/ - Verify user email
 * - GET /api/users/subscription/current/ - Get current subscription
 * - POST /api/users/subscription/upgrade/ - Upgrade subscription
 * - POST /api/users/subscription/cancel/ - Cancel subscription
 * 
 * @author nanthiniSanthanam
 * @version 2.1
 */

import React, { createContext, useState, useEffect, useContext } from 'react';
import { authService, subscriptionService } from '../services/api';

// Map subscription tiers to access levels
const ACCESS_LEVEL_MAP = {
  'free': 'intermediate',  // Free registered users get intermediate access
  'registered': 'intermediate',  // Registered users get intermediate access
  'basic': 'intermediate',  // Basic paid tier also gets intermediate access
  'premium': 'advanced'    // Premium paid tier gets advanced access
};

// Create context
const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [currentUser, setCurrentUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // New state for subscription
  const [subscription, setSubscription] = useState({
    tier: 'free',
    status: 'active',
    isActive: true,
    daysRemaining: 0
  });

  // Load user on mount and set up token refresh
  useEffect(() => {
    const loadUser = async () => {
      if (authService.isAuthenticated()) {
        try {
          // Try to get the current user with the stored token
          const response = await authService.getCurrentUser();
          setCurrentUser(response.data);
          
          // Get subscription information if authenticated
          try {
            const subscriptionResponse = await subscriptionService.getCurrentSubscription();
            setSubscription({
              tier: subscriptionResponse.data.tier || 'free',
              status: subscriptionResponse.data.status || 'active',
              isActive: subscriptionResponse.data.is_active !== false,
              daysRemaining: subscriptionResponse.data.days_remaining || 0,
              endDate: subscriptionResponse.data.end_date || null
            });
          } catch (subErr) {
            console.error('Error loading subscription:', subErr);
            // Set default subscription if can't load
            setSubscription({
              tier: 'free',
              status: 'active',
              isActive: true,
              daysRemaining: 0
            });
          }
          
          // Set up token refresh interval
          // Refresh token before it expires (e.g., every 25 minutes for 30 min tokens)
          const refreshInterval = setInterval(() => {
            authService.refreshToken()
              .catch(err => {
                console.error('Token refresh failed:', err);
                // If refresh fails, log the user out
                authService.logout();
                setCurrentUser(null);
                setSubscription({
                  tier: 'free',
                  status: 'active',
                  isActive: true,
                  daysRemaining: 0
                });
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
            
            // Try to get subscription after refresh
            try {
              const subscriptionResponse = await subscriptionService.getCurrentSubscription();
              setSubscription({
                tier: subscriptionResponse.data.tier || 'free',
                status: subscriptionResponse.data.status || 'active',
                isActive: subscriptionResponse.data.is_active !== false,
                daysRemaining: subscriptionResponse.data.days_remaining || 0,
                endDate: subscriptionResponse.data.end_date || null
              });
            } catch (subErr) {
              console.error('Error loading subscription after refresh:', subErr);
              setSubscription({
                tier: 'free',
                status: 'active',
                isActive: true,
                daysRemaining: 0
              });
            }
          } catch (refreshErr) {
            console.error('Token refresh failed:', refreshErr);
            // If refresh fails too, log the user out
            authService.logout();
            setSubscription({
              tier: 'free',
              status: 'active',
              isActive: true,
              daysRemaining: 0
            });
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



  // Resend verification email
const resendVerification = async (email) => {
  try {
    setError(null);
    await authService.resendVerification(email);
    return { success: true, message: 'Verification email sent successfully!' };
  } catch (err) {
    console.error('Email verification resend error:', err);
    const errorMsg = err.response?.data?.detail || 'Failed to resend verification email';
    setError(errorMsg);
    return { success: false, error: errorMsg };
  }
};




  // Login function
  const login = async (email, password, rememberMe = false) => {
    try {
      setError(null);
      // Pass remember me flag to determine token storage behavior
      const data = await authService.login({ email, password, rememberMe });
      
      // Get user details
      const userResponse = await authService.getCurrentUser();
      setCurrentUser(userResponse.data);
      
      // Get subscription details
      try {
        const subscriptionResponse = await subscriptionService.getCurrentSubscription();
        setSubscription({
          tier: subscriptionResponse.data.tier || 'free',
          status: subscriptionResponse.data.status || 'active',
          isActive: subscriptionResponse.data.is_active !== false,
          daysRemaining: subscriptionResponse.data.days_remaining || 0,
          endDate: subscriptionResponse.data.end_date || null
        });
      } catch (subErr) {
        console.error('Error loading subscription after login:', subErr);
        setSubscription({
          tier: 'free',
          status: 'active',
          isActive: true,
          daysRemaining: 0
        });
      }
      
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
    setSubscription({
      tier: 'free',
      status: 'active',
      isActive: true,
      daysRemaining: 0
    });
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

  // Subscription management functions
  
  // Upgrade subscription
  const upgradeSubscription = async (tier, paymentDetails = {}) => {
    try {
      setError(null);
      const response = await subscriptionService.upgradeSubscription(tier, paymentDetails);
      
      setSubscription({
        tier: response.data.tier,
        status: response.data.status,
        isActive: response.data.is_active !== false,
        daysRemaining: response.data.days_remaining || 0,
        endDate: response.data.end_date || null
      });
      
      return { 
        success: true, 
        message: `Successfully upgraded to ${tier} subscription!` 
      };
    } catch (err) {
      console.error('Subscription upgrade error:', err);
      const errorMsg = err.response?.data?.detail || 'Failed to upgrade subscription';
      setError(errorMsg);
      return { success: false, error: errorMsg };
    }
  };
  
  // Cancel subscription
  const cancelSubscription = async () => {
    try {
      setError(null);
      const response = await subscriptionService.cancelSubscription();
      
      setSubscription({
        ...subscription,
        status: 'cancelled',
        isActive: response.data.is_active !== false
      });
      
      return { 
        success: true, 
        message: 'Subscription cancelled. You will have access until the end of your billing period.' 
      };
    } catch (err) {
      console.error('Subscription cancellation error:', err);
      const errorMsg = err.response?.data?.detail || 'Failed to cancel subscription';
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
  
  // Check if user is a subscriber (has paid plan)
  const isSubscriber = () => {
    return isAuthenticated() && 
           subscription.tier !== 'free' && 
           subscription.isActive;
  };
  
  // Updated getAccessLevel function with the new logic
  const getAccessLevel = () => {
    if (!isAuthenticated()) {
      return 'basic'; // Unregistered users get basic access
    }
    
    // Use the mapping to determine access level
    const tier = subscription.isActive ? subscription.tier : 'free';
    return {
      'free': 'intermediate',  // Free registered users get intermediate access
      'basic': 'intermediate', // Basic paid tier also gets intermediate access
      'premium': 'advanced'    // Premium paid tier gets advanced access
    }[tier] || 'intermediate';
  };

  // Context value
  const value = {
    currentUser,
    subscription,
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
    resendVerification,
    // New subscription-related functions
    upgradeSubscription,
    cancelSubscription,
    isSubscriber,
    getAccessLevel,
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