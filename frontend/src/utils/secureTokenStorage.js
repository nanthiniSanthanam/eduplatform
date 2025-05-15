/**
 * File: frontend/src/utils/secureTokenStorage.js
 * Version: 1.0.1
 * Date: 2025-05-15 06:56:15
 * Author: cadsanthanam
 * 
 * Secure Token Storage Utility
 * 
 * Improved security for token management with the following features:
 * 1. Memory-first storage for access tokens (only persists when requested)
 * 2. Refresh token handling with HttpOnly cookie fallback support
 * 3. Token expiration management
 * 4. Automatic token validation and refresh
 * 
 * Dependencies:
 * - jwt-decode: For decoding JWT tokens
 */

// Fix for jwt-decode v4+ which uses named exports instead of default export
import { jwtDecode } from 'jwt-decode';
import { logWarning } from './logger';

// Configuration
const TOKEN_CONFIG = {
  ACCESS_TOKEN_KEY: 'accessToken',
  REFRESH_TOKEN_KEY: 'refreshToken',
  EXPIRY_KEY: 'tokenExpiry',
  PERSISTENCE_KEY: 'tokenPersistence',
  USE_HTTP_ONLY_COOKIES: false, // Set to true when backend supports it
};

// In-memory token storage (more secure than localStorage)
let memoryTokens = {
  access: null,
  refresh: null,
  expiry: null,
  shouldPersist: false
};

/**
 * Sets authentication data including tokens
 * @param {string} accessToken - JWT access token
 * @param {string} refreshToken - JWT refresh token
 * @param {boolean} rememberMe - Whether to persist tokens
 */
function setAuthData(accessToken, refreshToken, rememberMe = false) {
  try {
    // Decode the token to get expiration
    const decoded = jwtDecode(accessToken);
    const expiry = decoded.exp * 1000; // Convert to milliseconds
    
    // Store in memory first
    memoryTokens = {
      access: accessToken,
      refresh: refreshToken,
      expiry,
      shouldPersist: rememberMe
    };
    
    // If remember me is enabled, also store in localStorage
    if (rememberMe) {
      // Always store persistence setting
      localStorage.setItem(TOKEN_CONFIG.PERSISTENCE_KEY, 'true');
      localStorage.setItem(TOKEN_CONFIG.ACCESS_TOKEN_KEY, accessToken);
      
      // Store refresh token based on configuration
      if (!TOKEN_CONFIG.USE_HTTP_ONLY_COOKIES) {
        localStorage.setItem(TOKEN_CONFIG.REFRESH_TOKEN_KEY, refreshToken);
      }
      
      // Store expiry
      localStorage.setItem(TOKEN_CONFIG.EXPIRY_KEY, expiry.toString());
    }
  } catch (error) {
    logWarning('Error setting auth data:', { error });
    clearAuthData();
  }
}

/**
 * Updates the access token only
 * @param {string} accessToken - New JWT access token
 */
function updateAccessToken(accessToken) {
  try {
    // Decode the token to get expiration
    const decoded = jwtDecode(accessToken);
    const expiry = decoded.exp * 1000; // Convert to milliseconds
    
    // Update memory storage
    memoryTokens.access = accessToken;
    memoryTokens.expiry = expiry;
    
    // Update persistent storage if needed
    if (memoryTokens.shouldPersist || localStorage.getItem(TOKEN_CONFIG.PERSISTENCE_KEY) === 'true') {
      localStorage.setItem(TOKEN_CONFIG.ACCESS_TOKEN_KEY, accessToken);
      localStorage.setItem(TOKEN_CONFIG.EXPIRY_KEY, expiry.toString());
    }
  } catch (error) {
    logWarning('Error updating access token:', { error });
  }
}

/**
 * Gets a valid access token from memory or storage
 * @returns {string|null} Access token or null if not available
 */
function getValidToken() {
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
      const expiry = parseInt(localStorage.getItem(TOKEN_CONFIG.EXPIRY_KEY) || '0', 10);
      
      // Check if token is still valid
      if (expiry > Date.now()) {
        // Get from localStorage
        const accessToken = localStorage.getItem(TOKEN_CONFIG.ACCESS_TOKEN_KEY);
        
        // Update memory
        memoryTokens.access = accessToken;
        memoryTokens.expiry = expiry;
        memoryTokens.shouldPersist = true;
        
        return accessToken;
      }
    }
    
    // No valid token found
    return null;
  } catch (error) {
    logWarning('Error getting valid token:', { error });
    return null;
  }
}

/**
 * Gets the refresh token
 * @returns {string|null} Refresh token or null if not available
 */
function getRefreshToken() {
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
}

/**
 * Refreshes token expiry to maintain session
 */
function refreshTokenExpiry() {
  if (memoryTokens.expiry) {
    // JWT tokens have fixed expiry, but we can extend the session idle timeout
    const extendedTime = Date.now() + (30 * 60 * 1000); // 30 minutes from now
    
    // Only update if the token would expire sooner than our extension
    if (memoryTokens.expiry < extendedTime) {
      // No need to actually change the token, just update the time we'll check
      localStorage.setItem('lastActivity', Date.now().toString());
    }
  }
}

/**
 * Clears all authentication data
 */
function clearAuthData() {
  // Clear memory
  memoryTokens = {
    access: null,
    refresh: null,
    expiry: null,
    shouldPersist: false
  };
  
  // Clear localStorage
  localStorage.removeItem(TOKEN_CONFIG.ACCESS_TOKEN_KEY);
  localStorage.removeItem(TOKEN_CONFIG.REFRESH_TOKEN_KEY);
  localStorage.removeItem(TOKEN_CONFIG.EXPIRY_KEY);
  localStorage.removeItem(TOKEN_CONFIG.PERSISTENCE_KEY);
  localStorage.removeItem('lastActivity');
}

/**
 * Checks if token is valid
 * @returns {boolean} Whether a valid token exists
 */
function isTokenValid() {
  return getValidToken() !== null;
}

const secureTokenStorage = {
  setAuthData,
  updateAccessToken,
  getValidToken,
  getRefreshToken,
  refreshTokenExpiry,
  clearAuthData,
  isTokenValid
};

export default secureTokenStorage;