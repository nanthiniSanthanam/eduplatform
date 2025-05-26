/**
 * File: frontend/src/pages/instructor/InstructorDashboard.jsx
 * Version: 2.1.4
 * Date: 2025-05-25 15:53:02
 * Author: mohithasanthanam
 * Last Modified: 2025-05-25 15:53:02 UTC
 * 
 * Instructor Dashboard with Authentication Handling and Enhanced Course Creation Options
 * 
 * This component provides an instructor dashboard with key metrics and course management.
 * It includes improved authentication handling, redirects to login when needed,
 * and enhanced course creation/editing options with both traditional and wizard modes.
 * 
 * Key Improvements:
 * 1. Proper authentication checking before API calls
 * 2. Enhanced loading and error states
 * 3. Improved data fetching with retry capability
 * 4. Graceful handling of authentication failures
 * 5. Better user feedback during loading and errors
 * 6. Auto-redirect to login page on auth failure
 * 7. Fixed instructor role checking using AuthContext helper
 * 8. Fixed courses data handling for v2.7.0 API response format
 * 9. Added auth state guard to prevent race conditions
 * 10. Improved statistics mapping for consistent field names
 * 11. Added dual course creation options (wizard/traditional)
 * 12. Enhanced course editing with mode selection options
 * 13. Added editor mode persistence in localStorage
 * 
 * Connected files that need to be consistent:
 * - frontend/src/services/instructorService.js (provides data for dashboard)
 * - frontend/src/services/api.js (handles authentication)
 * - frontend/src/contexts/AuthContext.jsx (manages auth state)
 * - frontend/src/components/layouts/MainLayout.jsx (wrapper layout)
 * - frontend/src/components/common/LoadingScreen.jsx (loading indicator)
 * - frontend/src/components/common/Alert.jsx (error/info messages)
 * - frontend/src/components/common/Button.jsx (buttons with loading state)
 * - frontend/src/pages/instructor/CourseWizard.jsx (wizard mode course creation)
 * - frontend/src/pages/instructor/CreateCoursePage.jsx (traditional course creation)
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import MainLayout from '../../components/layouts/MainLayout';
import Card from '../../components/common/Card';
import Button from '../../components/common/Button';
import Alert from '../../components/common/Alert';
import LoadingScreen from '../../components/common/LoadingScreen';
import instructorService from '../../services/instructorService';
import api from '../../services/api';
import { useAuth } from '../../contexts/AuthContext'; // Using consistent relative path

const InstructorDashboard = () => {
  const [courses, setCourses] = useState([]);
  const [statistics, setStatistics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [refreshKey, setRefreshKey] = useState(0); // Used to trigger data refresh
  const navigate = useNavigate();
  const { isAuthenticated, isInstructor } = useAuth(); // Fixed: use isInstructor helper instead of currentUser
  
  // Refresh data function - can be called after operations that modify data
  const refreshData = () => {
    setRefreshKey(prevKey => prevKey + 1);
  };
  
  // Check authentication status before API calls
  const checkAuthBeforeFetch = useCallback(async () => {
    // Guard against auth race condition - wait until auth state is known
    if (isAuthenticated === null) {
      return false; // Auth state not yet determined
    }
    
    // Check if user is authenticated using the auth context
    if (!isAuthenticated) {
      console.log('User is not authenticated, redirecting to login page');
      navigate('/login?redirect=/instructor/dashboard');
      return false;
    }
    
    // Check if user is an instructor - Fixed: use isInstructor() helper
    if (!isInstructor()) {
      console.log('User is not an instructor, redirecting to home page');
      navigate('/');
      return false;
    }
    
    // Also check API's auth status as a fallback
    if (!api.isAuthenticated()) {
      try {
        // Try to refresh the token
        await api.auth.refreshToken();
        return true; // Token refreshed successfully
      } catch (error) {
        console.error('Failed to refresh token:', error);
        
        // Redirect to login page
        navigate('/login?redirect=/instructor/dashboard');
        return false; // Token refresh failed
      }
    }
    
    return true; // User is authenticated
  }, [isAuthenticated, isInstructor, navigate]); // Updated dependencies
  
  // Fetch instructor data function
  const fetchInstructorData = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Check authentication first
      const isAuthorized = await checkAuthBeforeFetch();
      if (!isAuthorized) return;
      
      // Fetch courses - Fixed: handle new API response format
      let normalizedCourses = [];
      try {
        const coursesResp = await instructorService.getAllCourses();
        
        // Handle both old array format and new { results: [...] } format
        normalizedCourses = Array.isArray(coursesResp)
          ? coursesResp
          : coursesResp?.results ?? [];
        
      } catch (error) {
        console.error('Failed to fetch courses:', error);
        
        if (error.status === 401) {
          // Authentication error, redirect to login
          navigate('/login?redirect=/instructor/dashboard');
          throw new Error('Authentication failed, please log in again');
        } else {
          // Other errors, display them
          throw error;
        }
      }
      
      // Fetch statistics
      let statsData = {};
      try {
        const rawStatsData = await instructorService.getInstructorStatistics();
        
        // Map statistics fields to handle potential field name differences
        statsData = {
          totalCourses: rawStatsData.totalCourses || rawStatsData.coursesCreated || normalizedCourses.length,
          totalStudents: rawStatsData.totalStudents || 0,
          totalRevenue: rawStatsData.totalRevenue || 0,
          recentEnrollments: rawStatsData.recentEnrollments || 0
        };
        
      } catch (error) {
        console.error('Failed to fetch statistics:', error);
        // Don't fail the whole dashboard if only stats fail
        statsData = {
          totalCourses: normalizedCourses.length || 0,
          totalStudents: 0,
          totalRevenue: 0,
          recentEnrollments: 0
        };
      }
      
      // Update state with fetched data
      setCourses(normalizedCourses);
      
      // Ensure totalCourses always reflects actual course count
      setStatistics({
        totalCourses: normalizedCourses.length,
        ...statsData,
      });
      
    } catch (error) {
      console.error('Error fetching instructor data:', error);
      
      // Format error message
      const errorMessage = error.message || 'Failed to load dashboard data';
      setError(errorMessage);
      
      // Set empty data
      setCourses([]);
      setStatistics(null);
    } finally {
      setLoading(false);
    }
  }, [checkAuthBeforeFetch, navigate]);
  
  // Fetch data on component mount and when refreshKey changes
  useEffect(() => {
    // Only fetch data if auth state is known (not null)
    if (isAuthenticated !== null) {
      fetchInstructorData();
    }
  }, [fetchInstructorData, refreshKey, isAuthenticated]);
  
  // Redirect if not authenticated or not an instructor
  useEffect(() => {
    // Guard against auth race condition
    if (isAuthenticated === null) {
      return; // Wait until auth state is determined
    }
    
    // If we have explicit authentication status from context
    if (isAuthenticated === false) {
      navigate('/login?redirect=/instructor/dashboard');
    } else if (isAuthenticated === true && !isInstructor()) {
      // Fixed: use isInstructor() helper for consistent checking
      navigate('/');
    }
  }, [isAuthenticated, isInstructor, navigate]);
  
  // ADDED: Function to handle new course creation with editor preference
  const handleCreateNewCourse = () => {
    // Check if user has a preferred editor mode
    const preferredMode = localStorage.getItem('editorMode') || 'wizard';
    
    if (preferredMode === 'wizard') {
      navigate('/instructor/courses/new');
    } else {
      navigate('/instructor/courses/traditional/new');
    }
  };
  
  // Handle course deletion
  const handleDeleteCourse = async (courseSlug) => {
    if (!window.confirm('Are you sure you want to delete this course? This action cannot be undone.')) {
      return;
    }
    
    try {
      await instructorService.deleteCourse(courseSlug);
      
      // Refresh courses list after deletion
      refreshData();
      
      // Show success message
      alert('Course deleted successfully');
    } catch (error) {
      console.error('Failed to delete course:', error);
      alert(`Failed to delete course: ${error.message || 'Unknown error'}`);
    }
  };
  
  // Show loading screen while auth state is being determined or data is loading
  if (isAuthenticated === null || loading) {
    return (
      <MainLayout>
        <LoadingScreen message="Loading instructor dashboard..." />
      </MainLayout>
    );
  }
  
  return (
    <MainLayout>
      <div className="container mx-auto px-4 py-8">
        <div className="flex flex-col md:flex-row justify-between items-center mb-8">
          <h1 className="text-3xl font-bold mb-4 md:mb-0">Instructor Dashboard</h1>
          
          {/* MODIFIED: Replaced single button with two options */}
          <div className="flex space-x-2">
            <Button 
              variant="primary" 
              onClick={() => {
                localStorage.setItem('editorMode', 'wizard');
                navigate('/instructor/courses/new');
              }}
            >
              Create with Wizard
            </Button>
            <Button 
              variant="outline" 
              onClick={() => {
                localStorage.setItem('editorMode', 'traditional');
                navigate('/instructor/courses/traditional/new');
              }}
            >
              Create Traditionally
            </Button>
          </div>
        </div>
        
        {error && (
          <Alert type="error" className="mb-6">
            {error}
            <div className="mt-2">
              <Button 
                size="small" 
                variant="outline" 
                onClick={refreshData}
              >
                Try Again
              </Button>
            </div>
          </Alert>
        )}
        
        {statistics && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <Card className="p-6 bg-primary-50">
              <h3 className="text-lg font-medium text-primary-700 mb-2">Total Courses</h3>
              <p className="text-3xl font-bold text-primary-900">{statistics.totalCourses || 0}</p>
            </Card>
            
            <Card className="p-6 bg-secondary-50">
              <h3 className="text-lg font-medium text-secondary-700 mb-2">Total Students</h3>
              <p className="text-3xl font-bold text-secondary-900">{statistics.totalStudents || 0}</p>
            </Card>
            
            <Card className="p-6 bg-tertiary-50">
              <h3 className="text-lg font-medium text-tertiary-700 mb-2">Total Revenue</h3>
              <p className="text-3xl font-bold text-tertiary-900">
                ${(statistics.totalRevenue || 0).toFixed(2)}
              </p>
            </Card>
            
            <Card className="p-6 bg-green-50">
              <h3 className="text-lg font-medium text-green-700 mb-2">Recent Enrollments</h3>
              <p className="text-3xl font-bold text-green-900">{statistics.recentEnrollments || 0}</p>
            </Card>
          </div>
        )}
        
        <Card className="p-6">
          <h2 className="text-xl font-bold mb-4">Your Courses</h2>
          
          {courses.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-gray-500 mb-4">You haven't created any courses yet.</p>
              {/* MODIFIED: Use dual creation options */}
              <div className="flex justify-center space-x-3">
                <Button 
                  variant="primary" 
                  onClick={() => {
                    localStorage.setItem('editorMode', 'wizard');
                    navigate('/instructor/courses/new');
                  }}
                >
                  Create with Wizard
                </Button>
                <Button 
                  variant="outline" 
                  onClick={() => {
                    localStorage.setItem('editorMode', 'traditional');
                    navigate('/instructor/courses/traditional/new');
                  }}
                >
                  Create Traditionally
                </Button>
              </div>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full border-collapse">
                <thead>
                  <tr className="bg-gray-100">
                    <th className="text-left p-4 border-b">Title</th>
                    <th className="text-left p-4 border-b">Status</th>
                    <th className="text-left p-4 border-b">Students</th>
                    <th className="text-left p-4 border-b">Revenue</th>
                    <th className="text-left p-4 border-b">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {courses.map((course) => (
                    <tr key={course.id} className="hover:bg-gray-50">
                      <td className="p-4 border-b">
                        <div className="flex items-center">
                          {course.thumbnail && (
                            <img 
                              src={course.thumbnail} 
                              alt={course.title} 
                              className="w-12 h-12 object-cover rounded-md mr-3"
                            />
                          )}
                          <div>
                            <h3 className="font-medium">{course.title}</h3>
                            <p className="text-sm text-gray-500">{course.category?.name || 'Uncategorized'}</p>
                          </div>
                        </div>
                      </td>
                      <td className="p-4 border-b">
                        <span 
                          className={`px-2 py-1 rounded-full text-xs font-medium
                            ${course.is_published 
                              ? 'bg-green-100 text-green-800' 
                              : 'bg-yellow-100 text-yellow-800'
                            }`}
                        >
                          {course.is_published ? 'Published' : 'Draft'}
                        </span>
                      </td>
                      <td className="p-4 border-b">
                        {course.student_count || 0}
                      </td>
                      <td className="p-4 border-b">
                        ${(course.revenue || 0).toFixed(2)}
                      </td>
                      {/* MODIFIED: Updated actions with both edit options */}
                      <td className="p-4 border-b">
                        <div className="flex space-x-2">
                          <Link to={`/instructor/courses/${course.slug}/edit`}>
                            <Button variant="outline" size="small">
                              Standard Edit
                            </Button>
                          </Link>
                          <Link to={`/instructor/courses/wizard/${course.slug}`}>
                            <Button variant="primary" size="small">
                              Wizard Edit
                            </Button>
                          </Link>
                          <Link to={`/instructor/courses/${course.slug}/curriculum`}>
                            <Button variant="outline" size="small">
                              Curriculum
                            </Button>
                          </Link>
                          <Button 
                            variant="danger" 
                            size="small"
                            onClick={() => handleDeleteCourse(course.slug)}
                          >
                            Delete
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      </div>
    </MainLayout>
  );
};

export default InstructorDashboard;