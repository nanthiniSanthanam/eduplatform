/**
 * File: frontend/src/pages/dashboard/DashboardPage.jsx
 * Purpose: Generic dashboard that redirects to role-specific dashboard
 * 
 * Key features:
 * 1. Automatically redirects users to their role-specific dashboard
 * 2. Serves as a central entry point for all authenticated users
 * 3. Shows loading state while checking user role
 * 4. Fallbacks to student dashboard if role detection fails
 * 
 * Implementation notes:
 * - Uses AuthContext to check user role
 * - Redirects to appropriate dashboard based on role
 * - Provides smooth transition with loading state
 */

import React, { useEffect } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

const DashboardPage = () => {
  const { currentUser, loading, isStudent, isInstructor, isAdmin } = useAuth();

  // Determine which dashboard to show based on user role
  const getDashboardPath = () => {
    if (isInstructor()) {
      return '/instructor/dashboard';
    } else if (isAdmin()) {
      return '/admin/dashboard';
    } else {
      // Default to student dashboard
      return '/student/dashboard';
    }
  };

  // If still loading, show a loading indicator
  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-700"></div>
        <span className="ml-3 text-primary-700">Loading...</span>
      </div>
    );
  }

  // Redirect to role-specific dashboard
  return <Navigate to={getDashboardPath()} replace />;
};

export default DashboardPage;