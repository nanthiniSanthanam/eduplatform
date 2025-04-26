/**
 * File: frontend/src/App.jsx
 * Purpose: Main application component that defines all routes
 * 
 * Key features:
 * 1. Role-based route protection (student, instructor, admin)
 * 2. Email verification support
 * 3. JWT authentication integration
 * 4. Dynamic content loading based on user role
 * 
 * Implementation notes:
 * - Uses updated ProtectedRoute component with role checking
 * - Integrates with AuthContext for authentication state
 * - Enables different dashboards based on user roles
 * - Maintains backward compatibility with existing routes
 */

import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';

// Public Pages
import HomePage from './pages/HomePage';
import LoginPage from './pages/auth/LoginPage';
import RegisterPage from './pages/auth/RegisterPage';
import CourseLandingPage from './pages/courses/CourseLandingPage';
import NotFoundPage from './pages/NotFoundPage';

// Protected Pages
import CourseContentPage from './pages/courses/CourseContentPage';
import AssessmentPage from './pages/courses/AssessmentPage';
import ProfilePage from './pages/user/ProfilePage';

// Dashboard Pages - Create these if they don't exist
import DashboardPage from './pages/dashboard/DashboardPage'; // Generic dashboard
import StudentDashboard from './pages/dashboard/StudentDashboard'; // Student-specific
import InstructorDashboard from './pages/dashboard/InstructorDashboard'; // Instructor-specific

// Authentication Pages - Create these if needed
import ForgotPasswordPage from './pages/auth/ForgotPasswordPage';
import ResetPasswordPage from './pages/auth/ResetPasswordPage';
import VerifyEmailPage from './pages/auth/VerifyEmailPage';

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
          <Route path="/" element={<HomePage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/forgot-password" element={<ForgotPasswordPage />} />
          <Route path="/reset-password/:token" element={<ResetPasswordPage />} />
          <Route path="/verify-email/:token?" element={<VerifyEmailPage />} />
          <Route path="/courses/:courseSlug" element={<CourseLandingPage />} />
          
          {/* Dashboard Routes - Role-specific */}
          <Route 
            path="/dashboard" 
            element={
              <ProtectedRoute>
                <DashboardPage />
              </ProtectedRoute>
            } 
          />
          
          <Route 
            path="/student/dashboard" 
            element={
              <ProtectedRoute requiredRoles={['student']}>
                <StudentDashboard />
              </ProtectedRoute>
            } 
          />
          
          <Route 
            path="/instructor/dashboard" 
            element={
              <ProtectedRoute requiredRoles={['instructor']}>
                <InstructorDashboard />
              </ProtectedRoute>
            } 
          />
          
          {/* Course Content Routes - Require Authentication */}
          <Route 
            path="/courses/:courseSlug/content/:moduleId/:lessonId" 
            element={
              <ProtectedRoute requireEmailVerified={true}>
                <CourseContentPage />
              </ProtectedRoute>
            } 
          />
          
          <Route 
            path="/courses/:courseSlug/assessment/:lessonId" 
            element={
              <ProtectedRoute requireEmailVerified={true}>
                <AssessmentPage />
              </ProtectedRoute>
            } 
          />
          
          {/* User Routes */}
          <Route 
            path="/profile" 
            element={
              <ProtectedRoute>
                <ProfilePage />
              </ProtectedRoute>
            } 
          />
          
          {/* 404 Route */}
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </AuthProvider>
    </Router>
  );
}

export default App;