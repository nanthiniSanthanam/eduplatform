/**
 * File: frontend/src/pages/courses/CreateModulePage.jsx
 * Purpose: Allows instructors to create new modules for their courses
 * 
 * This component:
 * 1. Provides a form for creating new course modules
 * 2. Validates module data
 * 3. Submits to the instructor API
 * 4. Shows success/error feedback
 * 
 * Access Level: Instructors only
 * 
 * Created by: Professor Santhanam
 * Last updated: 2025-05-04, 16:33:37
 */

import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import instructorService from "../../services/instructorService";
import { Container, Card, FormInput, Button, Alert } from '../../components/common';
import { useAuth } from '../../contexts/AuthContext';

const CreateModulePage = () => {
  const { courseSlug } = useParams();
  const navigate = useNavigate();
  const { currentUser } = useAuth();
  
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [order, setOrder] = useState(1);
  const [duration, setDuration] = useState('');
  
  const [loading, setLoading] = useState(false);
  const [courseLoading, setCourseLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [courseData, setCourseData] = useState(null);

  // Check if user is an instructor
  useEffect(() => {
    if (currentUser && currentUser.role !== 'instructor' && currentUser.role !== 'administrator' && currentUser.role !== 'admin') {
      navigate('/forbidden');
    }
  }, [currentUser, navigate]);

  // Fetch course data
  useEffect(() => {
    const fetchCourse = async () => {
      try {
        setCourseLoading(true);
        
        // Get course by slug - handling potential array response
        const response = await instructorService.getCourseBySlug(courseSlug);
        
        // Handle different response formats
        let courseData;
        if (response.data) {
          courseData = Array.isArray(response.data) ? response.data[0] : response.data;
        } else {
          courseData = Array.isArray(response) ? response[0] : response;
        }
        
        if (!courseData) {
          throw new Error("Course not found");
        }
        
        console.log("CreateModulePage: Loaded course data:", courseData);
        setCourseData(courseData);
        
        // Set initial order based on existing modules
        try {
          const modulesResponse = await instructorService.getModules(courseData.id);
          setOrder((modulesResponse.data?.length || 0) + 1);
        } catch (err) {
          console.error("Failed to fetch modules:", err);
          setOrder(1);
        }
        
        setCourseLoading(false);
      } catch (err) {
        console.error("Failed to fetch course:", err);
        setError("Failed to load course data");
        setCourseLoading(false);
      }
    };
    
    fetchCourse();
  }, [courseSlug]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!title) {
      setError("Module title is required");
      return;
    }
    
    try {
      setLoading(true);
      
      await instructorService.createModule({
        course: courseData.id,
        title,
        description,
        order,
        duration
      });
      
      setSuccess(true);
      
      // Redirect after brief delay
      setTimeout(() => {
        navigate(`/courses/${courseSlug}`);
      }, 2000);
      
    } catch (err) {
      console.error("Failed to create module:", err);
      setError("Failed to create module. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  if (courseLoading) {
    return (
      <Container>
        <div className="py-12 text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading course data...</p>
        </div>
      </Container>
    );
  }

  return (
    <div className="py-8">
      <Container>
        <div className="mb-6">
          <h1 className="text-3xl font-bold">Create Module</h1>
          {courseData && (
            <p className="text-gray-600 mt-2">
              Adding module to course: <strong>{courseData.title}</strong>
            </p>
          )}
        </div>
        
        {error && (
          <Alert type="error" className="mb-4">
            {error}
          </Alert>
        )}
        
        {success && (
          <Alert type="success" className="mb-4">
            Module created successfully! Redirecting...
          </Alert>
        )}
        
        <Card className="max-w-2xl mx-auto">
          <form onSubmit={handleSubmit} className="space-y-4">
            <FormInput
              label="Module Title"
              id="module-title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
              placeholder="e.g., Introduction to the Course"
            />
            
            <div className="form-group">
              <label htmlFor="description" className="block text-gray-700 font-medium mb-1">
                Description
              </label>
              <textarea
                id="description"
                rows={3}
                className="w-full p-2 border border-gray-300 rounded-md"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Describe what this module covers"
              ></textarea>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <FormInput
                label="Order in Course"
                id="order"
                type="number"
                min="1"
                value={order}
                onChange={(e) => setOrder(parseInt(e.target.value))}
                placeholder="e.g., 1"
              />
              
              <FormInput
                label="Estimated Duration"
                id="duration"
                value={duration}
                onChange={(e) => setDuration(e.target.value)}
                placeholder="e.g., 2 hours"
              />
            </div>
            
            <div className="flex justify-end space-x-3 pt-4">
              <Button
                type="button"
                variant="outlined"
                color="secondary"
                onClick={() => navigate(`/courses/${courseSlug}`)}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="contained"
                color="primary"
                disabled={loading}
              >
                {loading ? 'Creating Module...' : 'Create Module'}
              </Button>
            </div>
          </form>
        </Card>
      </Container>
    </div>
  );
};

export default CreateModulePage;