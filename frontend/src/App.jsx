/**
 * File: frontend/src/App.jsx
 * Purpose: Main application component that defines all routes
 * 
 * This component:
 * 1. Sets up routing for the entire application
 * 2. Defines access control for routes based on authentication and subscription
 * 3. Integrates with AuthContext for user management
 * 
 * Updates:
 * - Added content access level routes
 * - Added subscription-related routes
 * - Added certificate routes for paid users
 * - Fixed missing imports for subscription and certificate pages
 * 
 * Variables to modify:
 * None - routes are configured based on authentication state and roles
 * 
 * Route Access Levels:
 * - Public routes: Accessible to all users (homepage, about, login, register)
 * - Protected routes: Require basic authentication (course content, profile)
 * - Role-specific routes: Require specific user roles (admin dashboard, instructor dashboard)
 * - Subscription routes: Require premium subscription (certificates)
 * 
 * Created by: Professor Santhanam
 * Last updated: 2025-04-27, 16.08 pm
 */

import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';

// Layouts
import MainLayout from './components/layouts/MainLayout';

// Public Pages
import HomePage from './pages/HomePage';
import AboutPage from './pages/AboutPage';
import NotFoundPage from './pages/NotFoundPage';

// Auth Pages
import LoginPage from './pages/auth/LoginPage';
import RegisterPage from './pages/auth/RegisterPage';
import ForgotPasswordPage from './pages/auth/ForgotPasswordPage';
import ResetPasswordPage from './pages/auth/ResetPasswordPage';
import VerifyEmailPage from './pages/auth/VerifyEmailPage';

// Course Pages
import CourseLandingPage from './pages/courses/CourseLandingPage';
import CourseContentPage from './pages/courses/CourseContentPage';
import AssessmentPage from './pages/courses/AssessmentPage';
import CoursesListPage from './pages/courses/CoursesListPage';

// Dashboard Pages
import DashboardPage from './pages/dashboard/DashboardPage';
import StudentDashboard from './pages/dashboard/StudentDashboard';
import InstructorDashboard from './pages/dashboard/InstructorDashboard';
import AdminDashboard from './pages/dashboard/AdminDashboard';

// User Pages
import ProfilePage from './pages/user/ProfilePage';

// Subscription Pages
import PricingPage from './pages/subscription/PricingPage';
import CheckoutPage from './pages/subscription/CheckoutPage';
import SubscriptionSuccessPage from './pages/subscription/SubscriptionSuccessPage';

// Certificate Pages
import CertificatePage from './pages/certificates/CertificatePage';

// Protected Route Component
import ProtectedRoute from './components/routes/ProtectedRoute';

// Styles
import './App.css';

function App() {
  return (
    <Router>
      <AuthProvider>
        <Routes>
          {/* Public Routes */}
          <Route path="/" element={<MainLayout><HomePage /></MainLayout>} />
          <Route path="/about" element={<MainLayout><AboutPage /></MainLayout>} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/forgot-password" element={<ForgotPasswordPage />} />
          <Route path="/reset-password/:token" element={<ResetPasswordPage />} />
          <Route path="/verify-email/:token?" element={<VerifyEmailPage />} />
          
          {/* Course Landing Pages - Public but with tiered content */}
          <Route path="/courses/:courseSlug" element={<MainLayout><CourseLandingPage /></MainLayout>} />
          
          {/* Subscription Plans - Public but with auth redirects */}
          <Route path="/pricing" element={<MainLayout><PricingPage /></MainLayout>} />
          
          {/* Routes requiring basic authentication (registered users) */}
          <Route 
            path="/checkout/:planId" 
            element={
              <ProtectedRoute>
                <MainLayout><CheckoutPage /></MainLayout>
              </ProtectedRoute>
            } 
          />
          
          <Route 
            path="/subscription/success" 
            element={
              <ProtectedRoute>
                <MainLayout><SubscriptionSuccessPage /></MainLayout>
              </ProtectedRoute>
            } 
          />
          
          {/* Course Content - Requires authentication with content tiering */}
          <Route 
            path="/courses/:courseSlug/content/:moduleId/:lessonId" 
            element={
              <ProtectedRoute requireEmailVerified={true}>
                <MainLayout><CourseContentPage /></MainLayout>
              </ProtectedRoute>
            } 
          />
          
          <Route 
            path="/courses/:courseSlug/assessment/:lessonId" 
            element={
              <ProtectedRoute requireEmailVerified={true}>
                <MainLayout><AssessmentPage /></MainLayout>
              </ProtectedRoute>
            } 
          />
          
          {/* Dashboard Routes */}
          <Route 
            path="/dashboard" 
            element={
              <ProtectedRoute>
                <DashboardPage />
              </ProtectedRoute>
            } 
          />
          
          {/* Course List Page */}
          <Route 
            path="/courses" 
            element={
              <ProtectedRoute>
                <CoursesListPage />
              </ProtectedRoute>
            } 
          />



          {/* Role-Specific Dashboards */}
          <Route 
            path="/student/dashboard" 
            element={
              <ProtectedRoute requiredRoles={['student']}>
                <MainLayout><StudentDashboard /></MainLayout>
              </ProtectedRoute>
            } 
          />
          
          <Route 
            path="/instructor/dashboard" 
            element={
              <ProtectedRoute requiredRoles={['instructor']}>
                <MainLayout><InstructorDashboard /></MainLayout>
              </ProtectedRoute>
            } 
          />
          
          <Route 
            path="/admin/dashboard" 
            element={
              <ProtectedRoute requiredRoles={['admin']}>
                <MainLayout><AdminDashboard /></MainLayout>
              </ProtectedRoute>
            } 
          />
          
          {/* User Routes */}
          <Route 
            path="/profile" 
            element={
              <ProtectedRoute>
                <MainLayout><ProfilePage /></MainLayout>
              </ProtectedRoute>
            } 
          />
          
          {/* Certificate Routes - Only for paid subscribers */}
          <Route 
            path="/certificates/:certificateId" 
            element={
              <ProtectedRoute requiredSubscription="premium">
                <MainLayout>
                  <CertificatePage />
                </MainLayout>
              </ProtectedRoute>
            } 
          />
          
          {/* 404 Route */}
          <Route path="*" element={<MainLayout><NotFoundPage /></MainLayout>} />
        </Routes>
      </AuthProvider>
    </Router>
  );
}

export default App;