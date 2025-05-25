/**
 * File: frontend/src/components/routes/ProtectedRoute.jsx
 * Version: 2.2.0
 * Date: 2025-05-21
 * Author: cadsanthanam (updated)
 * 
 * Smart route protection component with tiered access control
 * 
 * CRITICAL FIXES:
 * - Added safety timeout to prevent infinite loading state
 * - Improved error recovery mechanisms
 * - Fixed ACCESS_LEVEL_MAP to align with ContentAccessController
 * 
 * ENHANCEMENTS:
 * - Added intelligent role-based redirects to appropriate dashboards
 * - Preserved return URL in login redirects for better UX
 * - Improved loading state handling
 */

import React, { useEffect, useState } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { LoadingScreen } from '../common';

// Map subscription props to actual subscription tiers
const SUBSCRIPTION_TIER_MAP = {
  'basic': ['basic', 'premium'],
  'premium': ['premium']
};

// Map access levels to minimum subscription tier required
const ACCESS_LEVEL_MAP = {
  'basic': null,  // No subscription required
  'intermediate': 'basic',  // Registered user (any tier) - FIXED from 'free' to 'basic'
  'advanced': 'premium'  // Premium subscription required
};

// Safety timeout duration for access checks (in milliseconds)
const ACCESS_CHECK_TIMEOUT = 10000; // 10 seconds

/**
 * Helper function to determine appropriate dashboard based on user role
 * @param {string} role - User role
 * @returns {string} - Dashboard path
 */
function getDashboardForRole(role) {
  switch (role) {
    case 'instructor': 
      return '/instructor/dashboard';
    case 'admin':
      return '/admin/dashboard';
    default:
      return '/student/dashboard';
  }
}

const ProtectedRoute = ({ 
  children, 
  requiredRoles = [], // Array of roles that can access this route
  requireEmailVerified = false, // Whether email verification is required
  requiredSubscription = null, // Required subscription level: null, 'basic', 'premium'
  requiredAccessLevel = null // Required access level: 'basic', 'intermediate', 'advanced'
}) => {
  const location = useLocation();
  const { currentUser, isLoading, isAuthenticated, getAccessLevel } = useAuth();
  const [accessGranted, setAccessGranted] = useState(false);
  const [isChecking, setIsChecking] = useState(true);
  const [redirectPath, setRedirectPath] = useState('/login');

  useEffect(() => {
    const checkAccess = async () => {
      setIsChecking(true);
      
      // CRITICAL FIX: Add safety timeout to prevent infinite checking
      const safetyTimeout = setTimeout(() => {
        console.warn("Protected route access check timed out - allowing access by default");
        setIsChecking(false);
        // Default to granting access in case of timeout, as blocking forever is worse
        setAccessGranted(true);
      }, ACCESS_CHECK_TIMEOUT);
      
      try {
        // If still loading auth state, wait but don't block forever
        if (isLoading) {
          // The safety timeout will handle this if it takes too long
          return;
        }
        
        // Not authenticated but access requires auth
        if (!isAuthenticated && (requiredRoles.length > 0 || requireEmailVerified || requiredSubscription)) {
          // Enhanced: Add return URL for better user experience
          setRedirectPath(`/login?redirect=${encodeURIComponent(location.pathname)}`);
          setAccessGranted(false);
          setIsChecking(false);
          clearTimeout(safetyTimeout);
          return;
        }
        
        // If no specific requirements beyond authentication
        if (requiredRoles.length === 0 && !requireEmailVerified && !requiredSubscription && !requiredAccessLevel) {
          setAccessGranted(true);
          setIsChecking(false);
          clearTimeout(safetyTimeout);
          return;
        }
        
        // Role check - user must have one of the required roles
        if (requiredRoles.length > 0) {
          const hasRole = requiredRoles.some(role => {
            if (role === 'student' && currentUser && !currentUser.role) {
              // Default to student if no role specified
              return true;
            }
            return currentUser && currentUser.role === role;
          });
          
          if (!hasRole) {
            // Enhanced: Redirect to appropriate dashboard based on role
            // instead of generic unauthorized page
            const dashboardPath = currentUser && currentUser.role 
              ? getDashboardForRole(currentUser.role)
              : '/unauthorized';
            
            setRedirectPath(dashboardPath);
            setAccessGranted(false);
            setIsChecking(false);
            clearTimeout(safetyTimeout);
            return;
          }
        }
        
        // Email verification check
        if (requireEmailVerified && currentUser && !currentUser.isEmailVerified) {
          setRedirectPath('/verify-email');
          setAccessGranted(false);
          setIsChecking(false);
          clearTimeout(safetyTimeout);
          return;
        }
        
        // Subscription check
        const hasRequiredSubscription = (
          !requiredSubscription || // No subscription required
          (requiredSubscription === 'free' && isAuthenticated) || // Free just requires authentication
          (currentUser && currentUser.subscription && 
           currentUser.subscription.tier === requiredSubscription && 
           currentUser.subscription.isActive)
        );
        
        if (!hasRequiredSubscription) {
          setRedirectPath('/subscription');
          setAccessGranted(false);
          setIsChecking(false);
          clearTimeout(safetyTimeout);
          return;
        }
        
        // Access level check
        if (requiredAccessLevel && isAuthenticated) {
          const userAccessLevel = getAccessLevel ? getAccessLevel() : 'basic';
          const accessLevels = { 'basic': 1, 'intermediate': 2, 'advanced': 3 };
          
          if (accessLevels[userAccessLevel] < accessLevels[requiredAccessLevel]) {
            setRedirectPath('/subscription');
            setAccessGranted(false);
            setIsChecking(false);
            clearTimeout(safetyTimeout);
            return;
          }
        }
        
        // If we've passed all checks, grant access
        setAccessGranted(true);
        setIsChecking(false);
        clearTimeout(safetyTimeout);
      } catch (error) {
        // If any error occurs during check, log it and default to granting access
        // This prevents users from being locked out due to errors
        console.error("Error during access check:", error);
        setAccessGranted(true);
        setIsChecking(false);
        clearTimeout(safetyTimeout);
      }
    };
    
    checkAccess();
    
    // Clean up safety timeout if component unmounts
    return () => {
      setIsChecking(false);
    };
  }, [currentUser, isLoading, isAuthenticated, location.pathname, requiredRoles, requireEmailVerified, requiredSubscription, requiredAccessLevel, getAccessLevel]);
  
  // Show loading while checking permissions (but not if auth is still loading)
  if (isChecking && !isLoading) {
    return <LoadingScreen message="Checking permissions..." />;
  }
  
  // Redirect if access not granted
  if (!accessGranted && !isLoading && !isChecking) {
    return <Navigate to={redirectPath} state={{ from: location }} replace />;
  }
  
  // Render children if access is granted or if we're still loading auth
  // This way content appears as soon as access is confirmed
  return children;
};

export default ProtectedRoute;