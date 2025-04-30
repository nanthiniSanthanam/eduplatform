/**
 * File: frontend/src/components/routes/ProtectedRoute.jsx
 * Purpose: Enhanced route protection component with tiered access control
 * 
 * This component:
 * 1. Protects routes from unauthenticated access
 * 2. Handles role-based route protection
 * 3. Handles subscription-level access protection
 * 4. Shows loading state while authentication status is being checked
 * 5. Redirects to appropriate pages when access is denied
 * 
 * Modifications for tiered access:
 * 1. Updated to work with enhanced AuthContext subscription state
 * 2. Added requiredAccessLevel prop for content access control
 * 3. Fixed subscription checking logic
 * 
 * Usage examples:
 * - Basic protection: <ProtectedRoute>...</ProtectedRoute>
 * - Role-based: <ProtectedRoute requiredRoles={['instructor']}>...</ProtectedRoute>
 * - Access-level-based: <ProtectedRoute requiredAccessLevel="advanced">...</ProtectedRoute>
 * - Subscription-based: <ProtectedRoute requiredSubscription="premium">...</ProtectedRoute>
 * - Email verification: <ProtectedRoute requireEmailVerified={true}>...</ProtectedRoute>
 * 
 * Variables to modify:
 * - SUBSCRIPTION_TIER_MAP: Maps subscription tiers to required subscription props
 * - ACCESS_LEVEL_MAP: Maps access levels to subscription tiers
 * 
 * @author nanthiniSanthanam
 * @version 2.0
 */

import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

// Map subscription props to actual subscription tiers
const SUBSCRIPTION_TIER_MAP = {
  'basic': ['basic', 'premium'],
  'premium': ['premium']
};

// Map access levels to minimum subscription tier required
const ACCESS_LEVEL_MAP = {
  'basic': null,  // No subscription required
  'intermediate': 'free',  // Registered user (any tier)
  'advanced': 'premium'  // Premium subscription required
};

const ProtectedRoute = ({ 
  children, 
  requiredRoles = [], // Array of roles that can access this route
  requireEmailVerified = false, // Whether email verification is required
  requiredSubscription = null, // Required subscription level: null, 'basic', 'premium'
  requiredAccessLevel = null // Required access level: 'basic', 'intermediate', 'advanced'
}) => {
  const { currentUser, isAuthenticated, loading, getAccessLevel, subscription } = useAuth();
  const location = useLocation();

  // Show loading indicator while checking authentication
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-700"></div>
        <span className="ml-3 text-primary-700">Loading...</span>
      </div>
    );
  }

  // Convert requiredAccessLevel to requiredSubscription if provided
  if (requiredAccessLevel && !requiredSubscription) {
    requiredSubscription = ACCESS_LEVEL_MAP[requiredAccessLevel];
  }

  // Redirect to login if not authenticated and route requires authentication
  if (!isAuthenticated() && (requiredRoles.length > 0 || requireEmailVerified || requiredSubscription)) {
    return <Navigate to="/login" state={{ from: location.pathname }} />;
  }

  // Check if email verification is required and the user's email is verified
  if (requireEmailVerified && currentUser && !currentUser.is_email_verified) {
    return <Navigate to="/verify-email" state={{ from: location.pathname }} />;
  }

  // Check if user has required role(s)
  if (requiredRoles.length > 0 && currentUser) {
    const hasRequiredRole = requiredRoles.includes(currentUser.role);
    
    if (!hasRequiredRole) {
      // Redirect to unauthorized page or dashboard based on role
      if (currentUser.role === 'student') {
        return <Navigate to="/student/dashboard" />;
      } else if (currentUser.role === 'instructor') {
        return <Navigate to="/instructor/dashboard" />;
      } else {
        return <Navigate to="/unauthorized" />;
      }
    }
  }

  // Check for subscription requirements
  if (requiredSubscription && currentUser) {
    // Get allowed tiers for this subscription requirement
    const allowedTiers = SUBSCRIPTION_TIER_MAP[requiredSubscription] || [];
    
    // Check if user's subscription is in the allowed tiers
    const hasRequiredSubscription = 
      (requiredSubscription === 'free' && isAuthenticated()) || // Free just requires authentication
      (allowedTiers.includes(subscription.tier) && subscription.isActive);
      
    if (!hasRequiredSubscription) {
      // Redirect to subscription page with return path
      return <Navigate to="/pricing" state={{ from: location.pathname }} />;
    }
  }

  // If requiredAccessLevel is specified, check access level
  if (requiredAccessLevel && isAuthenticated()) {
    const userAccessLevel = getAccessLevel();
    const accessLevelMap = { 'basic': 0, 'intermediate': 1, 'advanced': 2 };
    
    if (accessLevelMap[userAccessLevel] < accessLevelMap[requiredAccessLevel]) {
      // User doesn't have required access level
      return <Navigate to="/pricing" state={{ from: location.pathname }} />;
    }
  }

  // Render children if all checks pass
  return children;
};

export default ProtectedRoute;