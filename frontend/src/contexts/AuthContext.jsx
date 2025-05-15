/**
 * File: frontend/src/contexts/AuthContext.jsx
 * Version: 3.2.0
 * Date: 2025-08-13 08:21:36
 * Author: nanthiniSanthanam
 * 
 * Enhanced Authentication Context with Improved Session Persistence
 * 
 * Key Improvements:
 * 1. Uses authPersist utility for robust token management
 * 2. Implements automatic token refresh
 * 3. Handles session expiration gracefully
 * 4. Provides role-based session durations (longer for instructors)
 * 5. Optimized for frequent API operations in instructor workflows
 * 
 * This context provides:
 * - User authentication state management
 * - Login/logout functionality with persistent JWT tokens
 * - Role-based access control functions
 * - Subscription management for tiered access
 * - Automatic token refresh to maintain sessions
 * 
 * Usage:
 * const { currentUser, isAuthenticated, login, logout } = useAuth();
 */

import React, { createContext, useState, useContext, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import authPersist from '../utils/authPersist';

// Create the auth context
const AuthContext = createContext();

export const useAuth = () => {
  return useContext(AuthContext);
};

// Helper function to retrieve token regardless of naming convention (access or token)
const getStoredToken = () => {
  return authPersist.getValidToken();  // getValidToken already handles all cases
};

export const AuthProvider = ({ children }) => {
  // State for user data and authentication status
  const [currentUser, setCurrentUser] = useState(null);
  const [userRole, setUserRole] = useState(null);
  const [subscription, setSubscription] = useState(null);
  const [accessLevel, setAccessLevel] = useState('basic');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const navigate = useNavigate();

  // Access level mapping
  const ACCESS_LEVEL_MAP = {
    'free': 'basic',       // FIXED: free users have basic access 
    'registered': 'basic', // FIXED: registered users have basic access
    'basic': 'basic',      // FIXED: consistent naming
    'premium': 'advanced'  // Advanced still aligns with premium
  };

  // Check for existing valid token on mount
  useEffect(() => {
    const checkExistingAuth = async () => {
      try {
        setLoading(true);
        
        // Check if we have a valid token
        if (authPersist.isTokenValid()) {
          // Get stored user data
          const userData = authPersist.getUserData();
          
          if (userData) {
            console.log('Found existing valid auth session');
            setCurrentUser(userData);
            setIsAuthenticated(true);
            
            // Set user role
            const role = userData.role || authPersist.getUserRole();
            setUserRole(role);
            
            // Refresh token expiry to maintain session
            authPersist.refreshTokenExpiry();
            
            // Verify user data is still current by fetching from API
            try {
              const response = await api.auth.getCurrentUser();
              setCurrentUser(response);
              
              // Update stored user data
              const updatedAuthData = {
                token: authPersist.getValidToken(),
                refreshToken: authPersist.getRefreshToken(),
                user: response
              };
              authPersist.storeAuthData(updatedAuthData);
              
              // Try to fetch subscription data
              try {
                // Check if subscription service exists
                if (api.subscription && typeof api.subscription.getCurrentSubscription === 'function') {
                  const subscriptionData = await api.subscription.getCurrentSubscription();
                  setSubscription(subscriptionData);
                  
                  // Determine access level
                  const level = ACCESS_LEVEL_MAP[subscriptionData.tier?.toLowerCase() || 'free'] || 'basic';
                  setAccessLevel(level);
                } else {
                  console.warn('Subscription service not available, using default access level');
                  setSubscription({ tier: 'free', status: 'active' });
                  setAccessLevel('intermediate');
                }
              } catch (subError) {
                console.warn('Failed to fetch subscription data:', subError);
                // Set default access level
                setSubscription({ tier: 'free', status: 'active' });
                setAccessLevel('intermediate');
              }
            } catch (apiError) {
              console.warn('Failed to refresh user data:', apiError);
              // Continue with stored data since the token is still valid
            }
          } else {
            // We have a token but no user data, try to fetch user data
            try {
              const response = await api.auth.getCurrentUser();
              setCurrentUser(response);
              setUserRole(response.role);
              setIsAuthenticated(true);
              
              // Store the user data
              const authData = {
                token: authPersist.getValidToken(),
                refreshToken: authPersist.getRefreshToken(),
                user: response
              };
              
              // Store with extended session for instructors
              const expiryHours = authPersist.getSessionDuration(response);
              authPersist.storeAuthData(authData, expiryHours);
              
              // Try to fetch subscription data
              try {
                // Check if subscription service exists
                if (api.subscription && typeof api.subscription.getCurrentSubscription === 'function') {
                  const subscriptionData = await api.subscription.getCurrentSubscription();
                  setSubscription(subscriptionData);
                  
                  // Determine access level
                  const level = ACCESS_LEVEL_MAP[subscriptionData.tier?.toLowerCase() || 'free'] || 'basic';
                  setAccessLevel(level);
                } else {
                  console.warn('Subscription service not available, using default access level');
                  setSubscription({ tier: 'free', status: 'active' });
                  setAccessLevel('intermediate');
                }
              } catch (subError) {
                console.warn('Failed to fetch subscription data:', subError);
                // Set default access level
                setSubscription({ tier: 'free', status: 'active' });
                setAccessLevel('intermediate');
              }
            } catch (apiError) {
              console.error('Token valid but failed to get user:', apiError);
              // Token might be invalid despite our checks
              authPersist.clearAuthData();
              setCurrentUser(null);
              setUserRole(null);
              setIsAuthenticated(false);
            }
          }
        } else {
          // No valid token found
          authPersist.clearAuthData();
          setCurrentUser(null);
          setUserRole(null);
          setIsAuthenticated(false);
        }
      } catch (e) {
        console.error('Error during auth initialization:', e);
        authPersist.clearAuthData();
        setCurrentUser(null);
        setUserRole(null);
        setIsAuthenticated(false);
      } finally {
        setLoading(false);
      }
    };

    checkExistingAuth();
    
    // Set up periodic token refresh
    const refreshInterval = setInterval(async () => {
      if (authPersist.isTokenValid()) {
        // Get current time and token expiry
        const expiryString = localStorage.getItem('tokenExpiry');
        if (expiryString) {
          const expiry = new Date(expiryString);
          const now = new Date();
          const timeUntilExpiry = expiry.getTime() - now.getTime();
          
          // If token will expire in less than 5 minutes, refresh it
          if (timeUntilExpiry < 5 * 60 * 1000) {
            console.log('Token expiring soon, refreshing...');
            try {
              const refreshToken = authPersist.getRefreshToken();
              if (refreshToken) {
                await api.auth.refreshToken(refreshToken);
                console.log('Token refreshed successfully');
              }
            } catch (error) {
              console.error('Failed to refresh token:', error);
            }
          } else {
            // Just extend the expiration time
            authPersist.refreshTokenExpiry();
          }
        }
      }
    }, 15 * 60 * 1000); // Every 15 minutes
    
    return () => clearInterval(refreshInterval);
  }, []);

  // Login function
  const login = async (email, password, rememberMe = false) => {
    try {
      setError(null);
      setLoading(true);
      
      // Call login API
      const response = await api.auth.login({ email, password, rememberMe });
      
      // Extract token data
      const token = response.access || response.token;
      const refreshToken = response.refresh || response.refreshToken;
      
      if (!token) {
        throw new Error('Authentication failed - no token received');
      }
      
      // Get user data
      let userData;
      try {
        userData = await api.auth.getCurrentUser();
      } catch (userError) {
        console.error('Failed to fetch user data after login:', userError);
        throw new Error('Authentication successful but failed to load user data');
      }
      
      // Determine role and set extended expiry for instructors
      const role = userData.role || 'student';
      setUserRole(role);
      setCurrentUser(userData);
      setIsAuthenticated(true);
      
      // Store auth data with appropriate expiry
      const isInstructor = role === 'instructor' || role === 'admin';
      const expiryHours = isInstructor ? authPersist.INSTRUCTOR_EXPIRY_HOURS : authPersist.DEFAULT_EXPIRY_HOURS;
      
      authPersist.storeAuthData({
        token,
        refreshToken,
        user: userData
      }, expiryHours);
      
      // Fetch subscription data
      try {
        // Check if subscription service exists
        if (api.subscription && typeof api.subscription.getCurrentSubscription === 'function') {
          const subscriptionData = await api.subscription.getCurrentSubscription();
          setSubscription(subscriptionData);
          
          // Determine access level
          const level = ACCESS_LEVEL_MAP[subscriptionData.tier?.toLowerCase() || 'free'] || 'basic';
          setAccessLevel(level);
        } else {
          console.warn('Subscription service not available, using default access level');
          setSubscription({ tier: 'free', status: 'active' });
          setAccessLevel('intermediate');
        }
      } catch (subError) {
        console.warn('Failed to fetch subscription data:', subError);
        // Set default access level
        setSubscription({ tier: 'free', status: 'active' });
        setAccessLevel('intermediate');
      }
      
      // Make sure to return userData with role for the login component
      console.log("AuthContext returning user data with role:", role);
      return { ...userData, role };
    } catch (error) {
      console.error('Login error:', error);
      setError(error.message || 'Failed to login');
      throw error;
    } finally {
      setLoading(false);
    }
  };

  // Register function
  const register = async (userData) => {
    try {
      setError(null);
      const response = await api.auth.register(userData);
      return response;
    } catch (error) {
      console.error('Registration error:', error);
      setError(error.message || 'Failed to register');
      throw error;
    }
  };

  // Logout function
  const logout = (redirectPath = '/login') => {
    authPersist.clearAuthData();
    setCurrentUser(null);
    setUserRole(null);
    setSubscription(null);
    setAccessLevel('basic');
    setIsAuthenticated(false);
    navigate(redirectPath);
  };

  // Password reset functions
  const requestPasswordReset = async (email) => {
    try {
      await api.auth.requestPasswordReset(email);
      return true;
    } catch (error) {
      setError(error.message || 'Failed to request password reset');
      throw error;
    }
  };

  const resetPassword = async (token, password) => {
    try {
      await api.auth.resetPassword(token, password);
      return true;
    } catch (error) {
      setError(error.message || 'Failed to reset password');
      throw error;
    }
  };

  // Role checking functions
  const isInstructor = () => userRole === 'instructor';
  const isAdmin = () => userRole === 'admin' || userRole === 'administrator';
  const isStudent = () => userRole === 'student' || (!isInstructor() && !isAdmin());

  // Get access level for content based on subscription and login status
  const getAccessLevel = () => {
    if (!currentUser) return 'basic';
    return accessLevel;
  };

  // Check if user can access content at a given level
  const canAccessContent = (contentLevel) => {
    const userLevel = getAccessLevel();
    
    if (contentLevel === 'basic') return true;
    if (contentLevel === 'intermediate') return userLevel !== 'basic';
    if (contentLevel === 'advanced') return userLevel === 'advanced';
    
    return false;
  };

  // Context value
  const value = {
    currentUser,
    userRole,
    subscription,
    accessLevel,
    loading,
    isLoading: loading, // Add isLoading property that references loading for compatibility
    error,
    login,
    logout,
    register,
    requestPasswordReset,
    resetPassword,
    isInstructor,
    isAdmin,
    isStudent,
    isAuthenticated,
    getAccessLevel,
    canAccessContent
  };

  return (
    <AuthContext.Provider value={value}>
      {!loading && children}
    </AuthContext.Provider>
  );
};

export default AuthContext;
// END OF CODE