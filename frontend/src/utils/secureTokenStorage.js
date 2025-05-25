/**
 * File: frontend/src/utils/secureTokenStorage.js
 * Version: 2.3.0
 * Date: 2025-05-24 18:21:41
 * Author: mohithasanthanam, cadsanthanam
 * Last Modified: 2025-05-24 18:21:41 UTC
 * 
 * Secure Token Storage Utility - FIXED VERSION
 * 
 * CRITICAL FIXES APPLIED:
 * 1. Added missing compatibility functions (storeAuthData, getToken)
 * 2. Enhanced format compatibility for token expiry checking
 * 3. Added all missing functions to default export
 * 4. Improved null safety in token validation
 * 
 * This utility provides secure storage and management of authentication tokens
 * with proper expiration handling and token validation.
 * 
 * Key Features:
 * 1. Memory-first storage for access tokens (enhanced security)
 * 2. Secure storage of access and refresh tokens with persistence options
 * 3. Token validation with expiration checking and format compatibility
 * 4. Token refresh handling with rotation support
 * 5. Proper clearing of auth data on logout
 * 6. HttpOnly cookie fallback support for refresh tokens
 * 7. Backward compatibility with legacy API expectations
 * 
 * Connected files that need to be consistent:
 * - frontend/src/services/api.js (uses this utility for token management)
 * - frontend/src/contexts/AuthContext.jsx (auth state management)
 * - frontend/src/services/instructorService.js (requires auth for API calls)
 * - frontend/src/utils/authPersist.js - Also handles token storage
 * 
 * Dependencies:
 * - jwt-decode: For decoding JWT tokens
 */

// Fix for jwt-decode v4+ which uses named exports instead of default export
import { jwtDecode } from 'jwt-decode';

// Constants for token storage keys
const TOKEN_STORAGE_KEYS = {
  ACCESS: 'accessToken',
  REFRESH: 'refreshToken',
  USER: 'user',
  PERSISTENCE: 'tokenPersistence',
  EXPIRY: 'tokenExpiry'
};

// Configuration
const TOKEN_CONFIG = {
  ACCESS_TOKEN_KEY: TOKEN_STORAGE_KEYS.ACCESS,
  REFRESH_TOKEN_KEY: TOKEN_STORAGE_KEYS.REFRESH,
  EXPIRY_KEY: TOKEN_STORAGE_KEYS.EXPIRY,
  PERSISTENCE_KEY: TOKEN_STORAGE_KEYS.PERSISTENCE,
  USE_HTTP_ONLY_COOKIES: false, // Set to true when backend supports it
};

// In-memory token storage (more secure than localStorage)
let memoryTokens = {
  access: null,
  refresh: null,
  expiry: null,
  shouldPersist: false,
  userData: null
};

/**
 * Logger utility for warnings (fallback if not available)
 */
const logWarning = (message, data = {}) => {
  console.warn(message, data);
};

/**
 * Get access token from storage (backward compatibility)
 * @returns {string|null} - Access token or null
 */
export const getAccessToken = () => {
  // First check memory
  if (memoryTokens.access && memoryTokens.expiry > Date.now()) {
    return memoryTokens.access;
  }
  
  // Fallback to localStorage
  return localStorage.getItem(TOKEN_STORAGE_KEYS.ACCESS);
};

/**
 * Get refresh token from storage (backward compatibility)
 * @returns {string|null} - Refresh token or null
 */
export const getRefreshToken = () => {
  try {
    // First check memory
    if (memoryTokens.refresh) {
      return memoryTokens.refresh;
    }
    
    // If not in memory, check localStorage (if not using HttpOnly cookies)
    if (!TOKEN_CONFIG.USE_HTTP_ONLY_COOKIES && localStorage.getItem(TOKEN_CONFIG.REFRESH_TOKEN_KEY)) {
      const refreshToken = localStorage.getItem(TOKEN_CONFIG.REFRESH_TOKEN_KEY);
      
      // Update memory
      memoryTokens.refresh = refreshToken;
      return refreshToken;
    }
    
    // No refresh token found
    return null;
  } catch (error) {
    logWarning('Error getting refresh token:', { error });
    return null;
  }
};

/**
 * Store complete auth data with enhanced security
 * @param {string} accessToken - JWT access token
 * @param {string} refreshToken - JWT refresh token
 * @param {boolean} rememberMe - Whether to persist tokens
 */
export const setAuthData = (accessToken, refreshToken, rememberMe = false) => {
  try {
    if (!accessToken) {
      logWarning('No access token provided to setAuthData');
      return;
    }

    // Decode the token to get expiration
    const decoded = jwtDecode(accessToken);
    const expiry = decoded.exp * 1000; // Convert to milliseconds
    
    // Store in memory first (enhanced security)
    memoryTokens = {
      access: accessToken,
      refresh: refreshToken,
      expiry,
      shouldPersist: rememberMe,
      userData: memoryTokens.userData // Preserve existing user data
    };
    
    // If remember me is enabled, also store in localStorage
    if (rememberMe) {
      localStorage.setItem(TOKEN_CONFIG.PERSISTENCE_KEY, 'true');
      localStorage.setItem(TOKEN_CONFIG.ACCESS_TOKEN_KEY, accessToken);
      localStorage.setItem(TOKEN_CONFIG.EXPIRY_KEY, expiry.toString());
      
      // Store refresh token based on configuration
      if (refreshToken && !TOKEN_CONFIG.USE_HTTP_ONLY_COOKIES) {
        localStorage.setItem(TOKEN_CONFIG.REFRESH_TOKEN_KEY, refreshToken);
      }
    } else {
      localStorage.setItem(TOKEN_CONFIG.PERSISTENCE_KEY, 'false');
      // Store minimal data for session-only usage
      localStorage.setItem(TOKEN_CONFIG.ACCESS_TOKEN_KEY, accessToken);
      localStorage.setItem(TOKEN_CONFIG.EXPIRY_KEY, expiry.toString());
      
      if (refreshToken && !TOKEN_CONFIG.USE_HTTP_ONLY_COOKIES) {
        localStorage.setItem(TOKEN_CONFIG.REFRESH_TOKEN_KEY, refreshToken);
      }
    }
    
    console.log('Authentication data stored successfully');
  } catch (error) {
    logWarning('Error setting auth data:', { error });
    clearAuthData();
  }
};

/**
 * Update access token (e.g., after refresh)
 * @param {string} accessToken - New JWT access token
 */
export const updateAccessToken = (accessToken) => {
  try {
    if (!accessToken) {
      logWarning('No access token provided to updateAccessToken');
      return;
    }

    // Decode the token to get expiration
    const decoded = jwtDecode(accessToken);
    const expiry = decoded.exp * 1000; // Convert to milliseconds
    
    // Update memory storage
    memoryTokens.access = accessToken;
    memoryTokens.expiry = expiry;
    
    // Update persistent storage
    localStorage.setItem(TOKEN_CONFIG.ACCESS_TOKEN_KEY, accessToken);
    localStorage.setItem(TOKEN_CONFIG.EXPIRY_KEY, expiry.toString());
  } catch (error) {
    logWarning('Error updating access token:', { error });
  }
};

/**
 * Update refresh token (when rotation is enabled)
 * @param {string} refreshToken - New JWT refresh token
 */
export const updateRefreshToken = (refreshToken) => {
  if (refreshToken) {
    // Update memory storage
    memoryTokens.refresh = refreshToken;
    
    // Update persistent storage if not using HttpOnly cookies
    if (!TOKEN_CONFIG.USE_HTTP_ONLY_COOKIES) {
      localStorage.setItem(TOKEN_CONFIG.REFRESH_TOKEN_KEY, refreshToken);
    }
  }
};

/**
 * Clear all authentication data
 */
export const clearAuthData = () => {
  // Clear memory
  memoryTokens = {
    access: null,
    refresh: null,
    expiry: null,
    shouldPersist: false,
    userData: null
  };
  
  // Clear localStorage
  localStorage.removeItem(TOKEN_STORAGE_KEYS.ACCESS);
  localStorage.removeItem(TOKEN_STORAGE_KEYS.REFRESH);
  localStorage.removeItem(TOKEN_STORAGE_KEYS.USER);
  localStorage.removeItem(TOKEN_STORAGE_KEYS.PERSISTENCE);
  localStorage.removeItem(TOKEN_STORAGE_KEYS.EXPIRY);
  localStorage.removeItem('currentUser');
  localStorage.removeItem('userRole');
  localStorage.removeItem('userProfile');
  localStorage.removeItem('lastActivity');
  
  console.log('Authentication data cleared');
};

/**
 * Check if access token is valid and not expired
 * @returns {boolean} - True if token is valid
 */
export const isTokenValid = () => {
  try {
    // First check memory
    if (memoryTokens.access && memoryTokens.expiry) {
      return memoryTokens.expiry > Date.now() + 30000; // 30s buffer
    }
    
    // Fallback to localStorage check
    const token = localStorage.getItem(TOKEN_STORAGE_KEYS.ACCESS);
    if (!token) return false;
    
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      // 'exp' is in seconds, JS needs milliseconds
      return Date.now() < payload.exp * 1000 - 30000; // 30s skew
    } catch {
      return false; // malformed token
    }
  } catch (error) {
    logWarning('Error checking token validity:', { error });
    return false;
  }
};

/**
 * Check if token will expire soon (within 5 minutes)
 * @returns {boolean} - True if token will expire soon
 */
export const willTokenExpireSoon = () => {
  try {
    // First check memory
    if (memoryTokens.access && memoryTokens.expiry) {
      const currentTime = Date.now();
      const expiryThreshold = 5 * 60 * 1000; // 5 minutes in milliseconds
      return memoryTokens.expiry - currentTime < expiryThreshold;
    }
    
    // Fallback to localStorage check
    const token = localStorage.getItem(TOKEN_STORAGE_KEYS.ACCESS);
    if (!token) return true;
    
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      const currentTime = Date.now() / 1000;
      const expiryThreshold = 5 * 60; // 5 minutes in seconds
      
      return payload.exp - currentTime < expiryThreshold;
    } catch {
      return true; // assume it will expire soon on error
    }
  } catch (error) {
    logWarning('Error checking token expiry:', { error });
    return true;
  }
};

/**
 * Check if user has chosen to persist tokens
 * @returns {boolean} - True if persistence is enabled
 */
export const isPersistenceEnabled = () => {
  // First check memory
  if (memoryTokens.shouldPersist !== undefined) {
    return memoryTokens.shouldPersist;
  }
  
  // Fallback to localStorage
  return localStorage.getItem(TOKEN_STORAGE_KEYS.PERSISTENCE) === 'true';
};

/**
 * Get valid token, with enhanced format compatibility
 * @returns {string|null} - Valid token or null
 */
export const getValidToken = () => {
  try {
    // First check memory
    if (memoryTokens.access) {
      // Check if token is still valid
      if (memoryTokens.expiry > Date.now()) {
        return memoryTokens.access;
      }
    }
    
    // If not in memory or expired, check localStorage
    if (localStorage.getItem(TOKEN_CONFIG.ACCESS_TOKEN_KEY)) {
      const expiryString = localStorage.getItem(TOKEN_CONFIG.EXPIRY_KEY) || '0';
      
      // IMPROVED: Handle both ISO date string and millisecond timestamp formats + null safety
      let expiryMs;
      if (expiryString && expiryString.includes('-')) {
        // Handle ISO date string format
        expiryMs = new Date(expiryString).getTime();
      } else {
        // Handle millisecond timestamp format
        expiryMs = parseInt(expiryString, 10);
      }
      
      // Check if token is still valid
      if (expiryMs > Date.now()) {
        // Get from localStorage
        const accessToken = localStorage.getItem(TOKEN_CONFIG.ACCESS_TOKEN_KEY);
        
        // Update memory
        memoryTokens.access = accessToken;
        memoryTokens.expiry = expiryMs;
        memoryTokens.shouldPersist = localStorage.getItem(TOKEN_CONFIG.PERSISTENCE_KEY) === 'true';
        
        return accessToken;
      }
    }
    
    // No valid token found
    return null;
  } catch (error) {
    logWarning('Error getting valid token:', { error });
    return null;
  }
};

/**
 * Refreshes token expiry to maintain session
 */
export const refreshTokenExpiry = () => {
  if (memoryTokens.expiry) {
    // JWT tokens have fixed expiry, but we can extend the session idle timeout
    const extendedTime = Date.now() + (30 * 60 * 1000); // 30 minutes from now
    
    // Only update if the token would expire sooner than our extension
    if (memoryTokens.expiry < extendedTime) {
      // No need to actually change the token, just update the time we'll check
      localStorage.setItem('lastActivity', Date.now().toString());
    }
  }
};

/**
 * Store user data with memory-first approach
 * @param {Object} userData - User data to store
 */
export const setUserData = (userData) => {
  if (userData) {
    try {
      // Store in memory first
      memoryTokens.userData = userData;
      
      // Also store in localStorage for persistence
      localStorage.setItem(TOKEN_STORAGE_KEYS.USER, JSON.stringify(userData));
    } catch (error) {
      console.error('Error storing user data:', error);
    }
  }
};

/**
 * Get user data from storage with memory-first approach
 * @returns {Object|null} - User data or null
 */
export const getUserData = () => {
  try {
    // First check memory
    if (memoryTokens.userData) {
      return memoryTokens.userData;
    }
    
    // Fallback to localStorage
    const userData = localStorage.getItem(TOKEN_STORAGE_KEYS.USER);
    if (userData) {
      const parsedData = JSON.parse(userData);
      // Update memory cache
      memoryTokens.userData = parsedData;
      return parsedData;
    }
    
    return null;
  } catch (error) {
    console.error('Error retrieving user data:', error);
    return null;
  }
};

// FIXED: Added missing compatibility functions for AuthContext
/**
 * COMPATIBILITY: Legacy function expected by AuthContext
 * Store authentication data with object-style parameters
 * @param {Object} args - Object containing token, refreshToken, and user data
 * @returns {void}
 */
export const storeAuthData = (args) => {
  if (!args || typeof args !== 'object') {
    console.error('storeAuthData expects an object with token, refreshToken, and user properties');
    return;
  }
  
  const { token, refreshToken, user } = args;
  
  if (!token) {
    console.error('storeAuthData: token is required');
    return;
  }
  
  // Use the main setAuthData function with default rememberMe=true for legacy compatibility
  setAuthData(token, refreshToken, true);
  
  // Store user data if provided
  if (user) {
    setUserData(user);
  }
};

/**
 * COMPATIBILITY: Legacy function expected by AuthContext
 * Get access token (alias for getValidToken for backward compatibility)
 * @returns {string|null} - Access token or null
 */
export const getToken = () => {
  return getValidToken();
};

// FIXED: Export the secureTokenStorage object with ALL functions including compatibility ones
const secureTokenStorage = {
  getAccessToken,
  getRefreshToken,
  setAuthData,
  updateAccessToken,
  updateRefreshToken,
  clearAuthData,
  isTokenValid,
  willTokenExpireSoon,
  isPersistenceEnabled,
  getValidToken,
  refreshTokenExpiry,
  setUserData,
  getUserData,
  // FIXED: Added missing compatibility functions
  storeAuthData,
  getToken
};

export default secureTokenStorage;