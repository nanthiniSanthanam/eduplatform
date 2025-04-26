/**
 * File: frontend/src/pages/dashboard/InstructorDashboard.jsx
 * Purpose: Dashboard specifically for instructors
 * 
 * Key features:
 * 1. Shows courses created by the instructor
 * 2. Displays course statistics (enrollments, ratings)
 * 3. Provides course management actions
 * 4. Shows recent activities and student interactions
 * 
 * Implementation notes:
 * - Fetches data from API endpoints dynamically
 * - Shows loading states during data fetch
 * - Includes actions for course management
 * - Displays performance metrics for instructor
 */

import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { courseService } from '../../services/api';
import { useAuth } from '../../contexts/AuthContext';

const InstructorDashboard = () => {
  const { currentUser } = useAuth();
  const [courses, setCourses] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchInstructorData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Get courses created by instructor
        const coursesResponse = await courseService.getAllCourses({ 
          instructor: currentUser?.id
        });
        setCourses(coursesResponse.data || []);
        
        // Get instructor stats - this endpoint would need to be implemented in your API
        try {
          const statsResponse = await courseService.getInstructorStats();
          setStats(statsResponse.data || {
            total_students: 0,
            total_courses: 0,
            average_rating: 0,
            recent_enrollments: 0
          });
        } catch (statsError) {
          console.error('Could not fetch instructor stats:', statsError);
          // Set default stats if endpoint doesn't exist
          setStats({
            total_students: courses.reduce((sum, course) => sum + (course.students_count || 0), 0),
            total_courses: courses.length,
            average_rating: courses.reduce((sum, course) => sum + (course.avg_rating || 0), 0) / 
              (courses.length || 1),
            recent_enrollments: 0
          });
        }
        
      } catch (err) {
        console.error('Error fetching instructor data:', err);
        setError('Failed to load dashboard data. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    fetchInstructorData();
  }, [currentUser?.id]);

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
        <h1 className="text-3xl font-bold text-gray-900">Instructor Dashboard</h1>
        <p className="mt-2 text-gray-600">Manage your courses and track performance</p>
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

      {/* Quick Stats */}
      <div className="mb-8 bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold text-gray-800 mb-4">Overview</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-gray-50 p-4 rounded-lg">
            <p className="text-sm text-gray-500">Total Courses</p>
            <p className="text-2xl font-bold">{stats?.total_courses || courses.length}</p>
          </div>
          <div className="bg-gray-50 p-4 rounded-lg">
            <p className="text-sm text-gray-500">Total Students</p>
            <p className="text-2xl font-bold">{stats?.total_students || 0}</p>
          </div>
          <div className="bg-gray-50 p-4 rounded-lg">
            <p className="text-sm text-gray-500">Average Rating</p>
            <p className="text-2xl font-bold">{(stats?.average_rating || 0).toFixed(1)}</p>
          </div>
          <div className="bg-gray-50 p-4 rounded-lg">
            <p className="text-sm text-gray-500">New Enrollments</p>
            <p className="text-2xl font-bold">{stats?.recent_enrollments || 0}</p>
          </div>
        </div>
      </div>

      {/* Course Management */}
      <div className="mb-8">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-gray-800">My Courses</h2>
          <Link 
            to="/instructor/create-course" 
            className="bg-primary-600 text-white px-4 py-2 rounded hover:bg-primary-700"
          >
            Create New Course
          </Link>
        </div>

        {courses.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {courses.map(course => (
              <div key={course.id} className="bg-white rounded-lg shadow-md overflow-hidden">
                <img 
                  src={course.thumbnail || "/default-course.jpg"} 
                  alt={course.title} 
                  className="w-full h-48 object-cover"
                />
                <div className="p-4">
                  <h3 className="text-lg font-medium text-gray-900">{course.title}</h3>
                  
                  <div className="mt-2 flex justify-between">
                    <span className="text-sm text-gray-600">
                      {course.students_count || 0} students enrolled
                    </span>
                    <div className="flex items-center">
                      <svg className="w-4 h-4 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                      </svg>
                      <span className="ml-1 text-sm text-gray-600">
                        {course.avg_rating?.toFixed(1) || '0.0'} ({course.reviews_count || 0})
                      </span>
                    </div>
                  </div>
                  
                  <div className="mt-4 grid grid-cols-2 gap-2">
                    <Link 
                      to={`/instructor/courses/${course.slug}/edit`} 
                      className="bg-gray-200 text-gray-800 text-center py-2 rounded hover:bg-gray-300"
                    >
                      Edit Course
                    </Link>
                    <Link 
                      to={`/instructor/courses/${course.slug}/stats`} 
                      className="bg-gray-200 text-gray-800 text-center py-2 rounded hover:bg-gray-300"
                    >
                      View Stats
                    </Link>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow-md p-6 text-center">
            <p className="text-gray-600 mb-4">You haven't created any courses yet.</p>
            <Link 
              to="/instructor/create-course" 
              className="bg-primary-600 text-white px-4 py-2 rounded hover:bg-primary-700"
            >
              Create Your First Course
            </Link>
          </div>
        )}
      </div>
    </div>
  );
};

export default InstructorDashboard;