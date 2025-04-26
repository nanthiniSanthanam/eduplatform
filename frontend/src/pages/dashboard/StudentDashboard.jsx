/**
 * File: frontend/src/pages/dashboard/StudentDashboard.jsx
 * Purpose: Dashboard specifically for students
 * 
 * Key features:
 * 1. Shows enrolled courses with progress
 * 2. Displays user learning statistics
 * 3. Provides recommended courses based on interests
 * 4. Allows quick access to continue learning
 * 
 * Implementation notes:
 * - Fetches data from API endpoints dynamically
 * - Shows loading states during data fetch
 * - Handles errors gracefully with retry options
 * - Uses CourseCard component for consistent display
 */

import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { courseService, progressService } from '../../services/api';
import { useAuth } from '../../contexts/AuthContext';

const StudentDashboard = () => {
  const { currentUser } = useAuth();
  const [enrolledCourses, setEnrolledCourses] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [progressStats, setProgressStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Get enrolled courses
        const enrollmentsResponse = await progressService.getUserEnrollments();
        setEnrolledCourses(enrollmentsResponse.data || []);
        
        // Get progress statistics
        const statsResponse = await progressService.getUserProgressStats();
        setProgressStats(statsResponse.data || {
          completed_courses: 0,
          total_enrollments: 0,
          total_hours_spent: 0,
          assessments_completed: 0
        });
        
        // Get recommended courses
        const recommendationsResponse = await courseService.getAllCourses({ 
          recommended: true, 
          limit: 3 
        });
        setRecommendations(recommendationsResponse.data || []);
        
      } catch (err) {
        console.error('Error fetching dashboard data:', err);
        setError('Failed to load dashboard data. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-700"></div>
        <span className="ml-3 text-primary-700">Loading your dashboard...</span>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Welcome back, {currentUser?.first_name || 'Student'}!</h1>
        <p className="mt-2 text-gray-600">Continue your learning journey</p>
      </div>

      {error && (
        <div className="mb-8 bg-red-50 border-l-4 border-red-500 p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-700">{error}</p>
              <button 
                onClick={() => window.location.reload()} 
                className="mt-2 text-sm font-medium text-red-700 hover:text-red-600"
              >
                Retry
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Progress Summary */}
      <div className="mb-8 bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold text-gray-800 mb-4">Your Learning Progress</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-gray-50 p-4 rounded-lg">
            <p className="text-sm text-gray-500">Enrolled Courses</p>
            <p className="text-2xl font-bold">{progressStats?.total_enrollments || 0}</p>
          </div>
          <div className="bg-gray-50 p-4 rounded-lg">
            <p className="text-sm text-gray-500">Completed Courses</p>
            <p className="text-2xl font-bold">{progressStats?.completed_courses || 0}</p>
          </div>
          <div className="bg-gray-50 p-4 rounded-lg">
            <p className="text-sm text-gray-500">Hours Spent</p>
            <p className="text-2xl font-bold">{progressStats?.total_hours_spent?.toFixed(1) || 0}</p>
          </div>
          <div className="bg-gray-50 p-4 rounded-lg">
            <p className="text-sm text-gray-500">Assessments Completed</p>
            <p className="text-2xl font-bold">{progressStats?.assessments_completed || 0}</p>
          </div>
        </div>
      </div>

      {/* Enrolled Courses */}
      <div className="mb-8">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-gray-800">My Courses</h2>
          <Link to="/courses" className="text-primary-600 hover:text-primary-700">
            Browse All Courses
          </Link>
        </div>

        {enrolledCourses.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {enrolledCourses.map(enrollment => (
              <div key={enrollment.id} className="bg-white rounded-lg shadow-md overflow-hidden">
                <img 
                  src={enrollment.course.thumbnail || "/default-course.jpg"} 
                  alt={enrollment.course.title} 
                  className="w-full h-48 object-cover"
                />
                <div className="p-4">
                  <h3 className="text-lg font-medium text-gray-900">{enrollment.course.title}</h3>
                  <p className="mt-1 text-sm text-gray-500">
                    {enrollment.progress}% complete
                  </p>
                  
                  {/* Progress bar */}
                  <div className="mt-2 w-full bg-gray-200 rounded-full h-2.5">
                    <div 
                      className="bg-primary-600 h-2.5 rounded-full" 
                      style={{ width: `${enrollment.progress}%` }}
                    ></div>
                  </div>
                  
                  <div className="mt-4">
                    <Link 
                      to={`/courses/${enrollment.course.slug}/content/${enrollment.current_module_id || 1}/${enrollment.current_lesson_id || 1}`} 
                      className="block w-full bg-primary-600 text-center text-white py-2 rounded hover:bg-primary-700"
                    >
                      {enrollment.progress > 0 ? 'Continue Learning' : 'Start Learning'}
                    </Link>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow-md p-6 text-center">
            <p className="text-gray-600 mb-4">You haven't enrolled in any courses yet.</p>
            <Link 
              to="/courses" 
              className="bg-primary-600 text-white px-4 py-2 rounded hover:bg-primary-700"
            >
              Browse Courses
            </Link>
          </div>
        )}
      </div>

      {/* Recommended Courses */}
      <div>
        <h2 className="text-xl font-semibold text-gray-800 mb-4">Recommended For You</h2>
        
        {recommendations.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {recommendations.map(course => (
              <div key={course.id} className="bg-white rounded-lg shadow-md overflow-hidden">
                <img 
                  src={course.thumbnail || "/default-course.jpg"} 
                  alt={course.title} 
                  className="w-full h-48 object-cover"
                />
                <div className="p-4">
                  <h3 className="text-lg font-medium text-gray-900">{course.title}</h3>
                  <p className="mt-1 text-sm text-gray-500 line-clamp-2">
                    {course.short_description}
                  </p>
                  
                  <div className="mt-2 flex items-center">
                    <span className="text-sm text-gray-600">
                      By {course.instructor_name}
                    </span>
                  </div>
                  
                  <div className="mt-4 flex justify-between items-center">
                    <div className="flex items-center">
                      <svg className="w-4 h-4 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                      </svg>
                      <span className="ml-1 text-sm text-gray-600">
                        {course.avg_rating?.toFixed(1) || '0.0'} ({course.reviews_count || 0})
                      </span>
                    </div>
                    <span className="text-sm font-semibold">
                      {course.price === 0 ? 'Free' : `$${course.price}`}
                    </span>
                  </div>
                  
                  <div className="mt-4">
                    <Link 
                      to={`/courses/${course.slug}`} 
                      className="block w-full bg-primary-600 text-center text-white py-2 rounded hover:bg-primary-700"
                    >
                      View Course
                    </Link>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-600">No recommendations available at this time.</p>
        )}
      </div>
    </div>
  );
};

export default StudentDashboard;