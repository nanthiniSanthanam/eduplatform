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
 * Updated:
 * - Changed course management links to point to the course detail page
 * - Improved UI for course cards
 * - Fixed course deletion to use slug instead of ID
 * - Improved pagination functionality
 * 
 * Last updated: 2025-08-01, 10:42:47
 */

import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import instructorService from '../../services/instructorService';
import { useAuth } from '../../contexts/AuthContext';
import { Button } from '@mui/material';

const InstructorDashboard = () => {
  const { currentUser } = useAuth();
  const [courses, setCourses] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [deletingCourse, setDeletingCourse] = useState(null);
  const [deleteConfirmation, setDeleteConfirmation] = useState(false);
  const [pagination, setPagination] = useState({
    limit: 9,
    offset: 0,
    total: 0,
    hasMore: true
  });
  const [loadingMore, setLoadingMore] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchInstructorData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const coursesResponse = await instructorService.getAllCourses({
          limit: pagination.limit,
          offset: pagination.offset
        });
        
        if (coursesResponse && coursesResponse.results) {
          setCourses(coursesResponse.results);
          setPagination(prev => ({
            ...prev,
            total: coursesResponse.count || 0,
            hasMore: Boolean(coursesResponse.next)
          }));
        } else {
          setCourses(coursesResponse || []);
          setPagination(prev => ({
            ...prev,
            total: coursesResponse?.length || 0,
            hasMore: false
          }));
        }
        
        try {
          const statsResponse = await instructorService.getInstructorStatistics();
          setStats(statsResponse || {
            total_students: 0,
            total_courses: 0,
            average_rating: 0,
            recent_enrollments: 0
          });
        } catch (statsError) {
          console.error('Could not fetch instructor stats:', statsError);
          // Ensure courseCount is not 0 to avoid division by zero
          const courseCount = courses.length || 1;
          // Fix NaN in stats calculations
          setStats({
            total_students: courses.reduce((sum, course) => sum + (course.students_count || 0), 0),
            total_courses: courses.length,
            average_rating: courses.reduce((sum, course) => sum + (course.avg_rating || 0), 0) / courseCount,
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
  }, [currentUser?.id, pagination.offset, pagination.limit]);

  const handleDeleteCourse = async (courseId) => {
    try {
      setDeletingCourse(courseId);
      
      const courseToDelete = courses.find(c => c.id === courseId);
      if (!courseToDelete) {
        throw new Error('Course not found');
      }
      
      // Use the course slug for deletion rather than ID
      const slug = courseToDelete.slug;
      if (!slug) {
        throw new Error('Course slug not found');
      }
      
      await instructorService.deleteCourse(slug);
      
      setCourses(courses.filter(course => course.id !== courseId));
      setDeleteConfirmation(false);
      setDeletingCourse(null);
      
      setStats(prev => ({
        ...prev,
        total_courses: (prev.total_courses || courses.length) - 1
      }));
    } catch (error) {
      console.error('Error deleting course:', error);
      setError(`Failed to delete course: ${error.message || 'Unknown error occurred'}`);
      setDeletingCourse(null);
    }
  };

  const confirmDeleteCourse = (course) => {
    setDeletingCourse(course);
    setDeleteConfirmation(true);
  };

  const cancelDelete = () => {
    setDeletingCourse(null);
    setDeleteConfirmation(false);
  };

  const loadMoreCourses = async () => {
    if (!pagination.hasMore || loadingMore) return;
    
    try {
      setLoadingMore(true);
      const newOffset = pagination.offset + pagination.limit;
      
      const moreCoursesResponse = await instructorService.getAllCourses({
        limit: pagination.limit,
        offset: newOffset
      });
      
      if (moreCoursesResponse && moreCoursesResponse.results) {
        setCourses(prev => [...prev, ...moreCoursesResponse.results]);
        setPagination(prev => ({
          ...prev,
          offset: newOffset,
          total: moreCoursesResponse.count || prev.total,
          hasMore: Boolean(moreCoursesResponse.next)
        }));
      } else {
        setCourses(prev => [...prev, ...(moreCoursesResponse || [])]);
        setPagination(prev => ({
          ...prev,
          offset: newOffset,
          hasMore: false
        }));
      }
    } catch (error) {
      console.error('Error loading more courses:', error);
      setError('Failed to load more courses. Please try again.');
    } finally {
      setLoadingMore(false);
    }
  };

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
                onClick={() => setError(null)} 
                className="mt-2 text-sm font-medium text-red-700 hover:text-red-600"
              >
                Dismiss
              </button>
            </div>
          </div>
        </div>
      )}

      {deleteConfirmation && deletingCourse && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg max-w-md w-full">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Confirm Course Deletion</h3>
            <p className="text-gray-600 mb-6">
              Are you sure you want to delete the course "<span className="font-semibold">{deletingCourse.title}</span>"? 
              This action cannot be undone.
            </p>
            <div className="flex justify-end space-x-3">
              <button
                onClick={cancelDelete}
                className="px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300"
              >
                Cancel
              </button>
              <button
                onClick={() => handleDeleteCourse(deletingCourse.id)}
                className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
              >
                Delete Course
              </button>
            </div>
          </div>
        </div>
      )}

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

      <div className="mb-8">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-gray-800">My Courses</h2>
          <Button
            color="primary"
            variant="contained"
            className="ml-2"
            onClick={() => navigate('/instructor/courses/wizard')}
          >
            <svg className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            Create Course with Wizard
          </Button>
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
                      to={`/courses/${course.slug}`} 
                      className="bg-primary-600 text-white text-center py-2 rounded hover:bg-primary-700"
                    >
                      Manage Course
                    </Link>
                    <Link 
                      to={`/instructor/courses/${course.slug}/edit`} 
                      className="bg-gray-200 text-gray-800 text-center py-2 rounded hover:bg-gray-300"
                    >
                      Edit Course
                    </Link>
                  </div>
                  
                  <div className="mt-2">
                    <button
                      onClick={() => confirmDeleteCourse(course)}
                      className="w-full text-red-600 text-sm py-1 hover:text-red-700"
                    >
                      Delete Course
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow-md p-6 text-center">
            <p className="text-gray-600 mb-4">You haven't created any courses yet.</p>
            <Link 
              to="/instructor/courses/wizard" 
              className="bg-primary-600 text-white px-4 py-2 rounded hover:bg-primary-700"
            >
              Create Your First Course
            </Link>
          </div>
        )}
        
        {/* Pagination controls */}
        {pagination.hasMore && (
          <div className="mt-8 text-center">
            <button
              onClick={loadMoreCourses}
              disabled={loadingMore}
              className="bg-white border border-gray-300 text-gray-700 px-4 py-2 rounded shadow hover:bg-gray-50 disabled:opacity-50"
            >
              {loadingMore ? (
                <span className="flex items-center justify-center">
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-gray-700" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Loading more...
                </span>
              ) : 'Load More Courses'}
            </button>
          </div>
        )}
        
        {/* Pagination info */}
        <div className="mt-4 text-center text-sm text-gray-600">
          Showing {courses.length} of {pagination.total} total courses
        </div>
      </div>
    </div>
  );
};

export default InstructorDashboard;