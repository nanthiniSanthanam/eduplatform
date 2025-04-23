import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import HomePage from './pages/HomePage';
import LoginPage from './pages/auth/LoginPage';
import RegisterPage from './pages/auth/RegisterPage';
import CourseLandingPage from './pages/courses/CourseLandingPage';
import CourseContentPage from './pages/courses/CourseContentPage';
import AssessmentPage from './pages/courses/AssessmentPage';
import ProfilePage from './pages/user/ProfilePage';
import NotFoundPage from './pages/NotFoundPage';
import './App.css';
import ProtectedRoute from './components/routes/ProtectedRoute';

function App() {
  return (
    <Router>
      <AuthProvider>
        <Routes>
          {/* Public Routes */}
          <Route path="/" element={<HomePage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          
          {/* Generic Course Routes */}
          <Route path="/courses/:courseSlug" element={<CourseLandingPage />} />
          <Route 
            path="/courses/:courseSlug/content/:moduleId/:lessonId" 
            element={
              <ProtectedRoute>
                <CourseContentPage />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/courses/:courseSlug/assessment/:lessonId" 
            element={
              <ProtectedRoute>
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