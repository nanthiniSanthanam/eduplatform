/**
 * File: frontend/src/components/ProtectedRoute.jsx
 * Purpose: Route protection component with role-based access control
 * 
 * This component:
 * 1. Protects routes from unauthenticated access
 * 2. Handles role-based route protection
 * 3. Shows loading state while authentication status is being checked
 * 4. Redirects to login with return path when access is denied
 * 
 * Modifications for new backend:
 * 1. Added role-based access control
 * 2. Enhanced error handling for unauthenticated users
 * 3. Added email verification check option
 * 
 * Usage examples:
 * - Basic protection: <ProtectedRoute>...</ProtectedRoute>
 * - Role-based: <ProtectedRoute requiredRoles={['instructor']}>...</ProtectedRoute>
 * - Verification check: <ProtectedRoute requireEmailVerified={true}>...</ProtectedRoute>
 */

import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext'; // Fix the import path if needed

const ProtectedRoute = ({ 
  children, 
  requiredRoles = [], // Array of roles that can access this route
  requireEmailVerified = false // Whether email verification is required
}) => {
  const { currentUser, isAuthenticated, loading } = useAuth();
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

  // Redirect to login if not authenticated
  if (!isAuthenticated()) {
    return <Navigate to="/login" state={{ from: location.pathname }} />;
  }

  // Check if email verification is required and the user's email is verified
  if (requireEmailVerified && !currentUser.is_email_verified) {
    return <Navigate to="/verify-email" state={{ from: location.pathname }} />;
  }

  // Check if user has required role(s)
  if (requiredRoles.length > 0) {
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

  // Render children if all checks pass
  return children;
};

export default ProtectedRoute;