/**
 * File: frontend/src/App.jsx
 * Version: 2.2.0
 * Date: 2025-05-11 16:41:04
 * Author: cadsanthanam
 * 
 * Enhanced Main Application Component with Improved Content Access Control
 * 
 * Key Improvements:
 * 1. Support for both ID and slug-based course routes
 * 2. Integration with authPersist for reliable authentication
 * 3. More consistent route naming patterns
 * 4. Enhanced protected route implementation
 * 5. Better organization of route groups
 * 6. Consistent role checks for admin/instructor routes
 * 7. Smart content access control for tiered educational content
 * 
 * This component:
 * 1. Sets up routing for the entire application
 * 2. Defines access control for routes based on authentication and subscription
 * 3. Integrates with AuthContext for user management
 * 4. Implements tiered content access (basic/intermediate/advanced)
 * 
 * Route Access Levels:
 * - Public routes: Accessible to all users (homepage, about, login, register)
 * - Protected routes: Require basic authentication (course content, profile)
 * - Role-specific routes: Require specific user roles (admin dashboard, instructor dashboard)
 * - Subscription routes: Require premium subscription (certificates)
 * - Tiered content routes: Access based on content level and user status
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
import CreateLessonPage from './pages/courses/CreateLessonPage';
import InstructorCourseDetailPage from './pages/courses/InstructorCourseDetailPage';
import CreateModulePage from './pages/courses/CreateModulePage';
import CreateCoursePage from './pages/instructor/CreateCoursePage';
import CourseWizard from './pages/instructor/CourseWizard';
import EditCoursePage from './pages/instructor/EditCoursePage';

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

// Route Components
import ProtectedRoute from './components/routes/ProtectedRoute';
import CourseContentRouteChecker from './components/routes/CourseContentRouteChecker';

// Styles
import './Index.css';

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
          <Route path="/verify-email" element={<VerifyEmailPage />} />
          
          {/* Course Landing Pages - Public but with tiered content */}
          <Route path="/courses/:courseSlug" element={<MainLayout><CourseLandingPage /></MainLayout>} />
          
          {/* Module Detail Page - Public view for browsing course structure */}
          <Route path="/courses/:courseSlug/modules/:moduleId" element={<MainLayout><CourseContentPage previewMode={true} /></MainLayout>} />
          
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
          
          {/* Course Content - Smart access control based on content tier */}
          <Route 
            path="/courses/:courseSlug/content/:moduleId/:lessonId" 
            element={<CourseContentRouteChecker />} 
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
                <MainLayout><CoursesListPage /></MainLayout>
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
              <ProtectedRoute requiredRoles={['instructor', 'admin']}>
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
          
          {/* Instructor Course Management - Support for both ID and slug-based routes */}
          
          {/* Course Creation */}
          <Route 
            path="/instructor/create-course" 
            element={
              <ProtectedRoute requiredRoles={['instructor', 'admin']}>
                <MainLayout><CreateCoursePage /></MainLayout>
              </ProtectedRoute>
            } 
          />
          
          <Route 
            path="/instructor/courses/new" 
            element={
              <ProtectedRoute requiredRoles={['instructor', 'admin']}>
                <MainLayout><CreateCoursePage /></MainLayout>
              </ProtectedRoute>
            } 
          />
          
          {/* Course Wizard - Supports both new courses and editing by slug */}
          <Route 
            path="/instructor/courses/wizard" 
            element={
              <ProtectedRoute requiredRoles={['instructor', 'admin']}>
                <MainLayout><CourseWizard /></MainLayout>
              </ProtectedRoute>
            } 
          />
          
          <Route 
            path="/instructor/courses/wizard/:courseSlug" 
            element={
              <ProtectedRoute requiredRoles={['instructor', 'admin']}>
                <MainLayout><CourseWizard /></MainLayout>
              </ProtectedRoute>
            } 
          />
          
          {/* Course Details - Support both slug and ID-based routes */}
          <Route 
            path="/instructor/courses/:courseIdentifier" 
            element={
              <ProtectedRoute requiredRoles={['instructor', 'admin']}>
                <MainLayout><InstructorCourseDetailPage /></MainLayout>
              </ProtectedRoute>
            } 
          />
          
          {/* Course Editing - Support both slug and ID-based routes */}
          <Route 
            path="/instructor/courses/:courseIdentifier/edit" 
            element={
              <ProtectedRoute requiredRoles={['instructor', 'admin']}>
                <MainLayout><EditCoursePage /></MainLayout>
              </ProtectedRoute>
            } 
          />
          
          {/* Course Management - Using more descriptive slug-based URL parameter */}
          <Route 
            path="/instructor/courses/:courseIdentifier/manage" 
            element={
              <ProtectedRoute requiredRoles={['instructor', 'admin']}>
                <MainLayout><InstructorCourseDetailPage /></MainLayout>
              </ProtectedRoute>
            } 
          />
          
          {/* Module Creation */}
          <Route 
            path="/instructor/courses/:courseIdentifier/modules/new" 
            element={
              <ProtectedRoute requiredRoles={['instructor', 'admin']}>
                <MainLayout><CreateModulePage /></MainLayout>
              </ProtectedRoute>
            } 
          />
          
          {/* Legacy routes that use slug format - keep for backward compatibility */}
          <Route 
            path="/courses/:courseSlug/modules/create" 
            element={
              <ProtectedRoute requiredRoles={['instructor', 'admin']}>
                <MainLayout><CreateModulePage /></MainLayout>
              </ProtectedRoute>
            } 
          />
          
          <Route 
            path="/courses/:courseSlug/modules/:moduleId/lessons/create" 
            element={
              <ProtectedRoute requiredRoles={['instructor', 'admin']}>
                <MainLayout><CreateLessonPage /></MainLayout>
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