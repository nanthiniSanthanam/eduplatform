/**
 * File: frontend/src/pages/instructor/CreateCoursePage.jsx
 * Version: 2.1.0
 * Date: 2025-08-01
 * Author: nanthiniSanthanam
 * 
 * Enhanced Course Creation Page with Authentication Persistence
 * 
 * Key Improvements:
 * 1. Integration with authPersist for reliable authentication
 * 2. Enhanced error handling with detailed user feedback
 * 3. Better form validation with immediate feedback
 * 4. Improved category handling
 * 5. Added slug-based redirect after course creation
 * 6. Proper FormData handling for file uploads
 * 7. Improved thumbnail preview functionality
 * 
 * This component provides a simplified form for instructors to create new courses.
 * After initial creation, users are redirected to the course detail page or wizard
 * for further editing.
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import instructorService from '../../services/instructorService';
import api from '../../services/api';
import { useAuth } from '../../contexts/AuthContext';
import authPersist from '../../utils/authPersist';

// Direct imports to avoid casing issues
import Container from '../../components/common/Container';
import Card from '../../components/common/Card';
import FormInput from '../../components/common/FormInput';
import Button from '../../components/common/Button';
import Alert from '../../components/common/Alert';
import LoadingScreen from '../../components/common/LoadingScreen';
import MainLayout from '../../components/layouts/MainLayout';

const CreateCoursePage = () => {
  const { currentUser } = useAuth();
  const navigate = useNavigate();
  
  // Form state
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    category_id: '',
    level: 'beginner',
    price: '',
    has_certificate: false
  });
  
  // UI state
  const [thumbnail, setThumbnail] = useState(null);
  const [thumbnailPreview, setThumbnailPreview] = useState(null);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(false);
  const [fetchingCategories, setFetchingCategories] = useState(true);
  const [error, setError] = useState(null);
  const [formErrors, setFormErrors] = useState({});
  const [success, setSuccess] = useState(false);
  
  // Fetch categories on component mount
  useEffect(() => {
    async function fetchCategories() {
      try {
        setFetchingCategories(true);
        const cats = await api.category.getAllCategories();
        setCategories(cats || []);
      } catch (err) {
        console.error("Error fetching categories:", err);
        setError("Failed to load categories. Please refresh the page.");
      } finally {
        setFetchingCategories(false);
      }
    }
    
    // Refresh auth token
    if (authPersist && typeof authPersist.isTokenValid === 'function' && 
        typeof authPersist.refreshTokenExpiry === 'function') {
      if (authPersist.isTokenValid()) {
        authPersist.refreshTokenExpiry();
      }
    }
    
    fetchCategories();
  }, []);

  // Handle input change
  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    const inputValue = type === 'checkbox' ? checked : value;
    
    setFormData({
      ...formData,
      [name]: inputValue
    });
    
    // Clear error for this field when user edits
    if (formErrors[name]) {
      setFormErrors({
        ...formErrors,
        [name]: null
      });
    }
  };
  
  // Handle thumbnail file selection
  const handleThumbnailChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setThumbnail(file);
      
      // Create a preview URL for the thumbnail
      const reader = new FileReader();
      reader.onloadend = () => {
        setThumbnailPreview(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };
  
  // Validate form
  const validateForm = () => {
    const errors = {};
    
    if (!formData.title || formData.title.trim() === '') {
      errors.title = 'Course title is required';
    }
    
    if (!formData.description || formData.description.trim() === '') {
      errors.description = 'Course description is required';
    }
    
    if (!formData.category_id) {
      errors.category_id = 'Category is required';
    }
    
    if (formData.price && isNaN(parseFloat(formData.price))) {
      errors.price = 'Price must be a valid number';
    }
    
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validate form
    if (!validateForm()) {
      return;
    }
    
    try {
      setLoading(true);
      setError(null);
      
      // Create FormData for multipart submission
      const formDataObj = new FormData();
      
      // Add all scalar fields
      Object.entries(formData).forEach(([key, value]) => {
        // Handle empty price specifically
        if (key === 'price') {
          formDataObj.append(key, value === '' ? '0' : value);
        } else {
          formDataObj.append(key, value);
        }
      });
      
      // Add thumbnail file if present
      if (thumbnail) {
        formDataObj.append('thumbnail', thumbnail);
      }
      
      // Create course with FormData
      const createdCourse = await instructorService.createCourse(formDataObj);
      
      setSuccess(true);
      
      // Navigate to course detail/edit page
      setTimeout(() => {
        if (createdCourse && createdCourse.slug) {
          // Navigate to course wizard for continued editing
          navigate(`/instructor/courses/wizard/${createdCourse.slug}`);
        } else if (createdCourse && createdCourse.id) {
          // Fallback to ID-based navigation if slug isn't available
          navigate(`/instructor/courses/${createdCourse.id}/edit`);
        } else {
          // If no ID or slug, go to instructor dashboard
          navigate('/instructor/dashboard');
        }
      }, 1500);
    } catch (err) {
      console.error('Error creating course:', err);
      
      // Extract detailed error message if available
      let errorMessage = 'Failed to create course.';
      
      if (err.details) {
        // Format detailed API errors
        if (typeof err.details === 'object') {
          const errorDetails = Object.entries(err.details).map(([key, value]) => {
            const errorText = Array.isArray(value) ? value.join(', ') : value;
            return `${key}: ${errorText}`;
          });
          
          if (errorDetails.length > 0) {
            errorMessage = errorDetails.join('\n');
          }
        } else if (typeof err.details === 'string') {
          errorMessage = err.details;
        }
      } else if (err.message) {
        errorMessage = err.message;
      }
      
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };
  
  // If fetching initial data
  if (fetchingCategories) {
    return (
      <MainLayout>
        <Container>
          <LoadingScreen message="Loading categories..." />
        </Container>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <div className="py-8">
        <Container>
          <div className="mb-6">
            <h1 className="text-3xl font-bold">Create New Course</h1>
            <p className="text-gray-600 mt-2">
              Start with the basics. You can add more details after creating the course.
            </p>
          </div>
          
          {error && (
            <Alert type="error" className="mb-4">
              {error}
            </Alert>
          )}
          
          {success && (
            <Alert type="success" className="mb-4">
              Course created successfully! Redirecting to course editor...
            </Alert>
          )}
          
          <Card className="max-w-3xl mx-auto p-6">
            <form onSubmit={handleSubmit} className="space-y-6" encType="multipart/form-data">
              <FormInput
                label="Course Title"
                name="title"
                id="course-title"
                value={formData.title}
                onChange={handleChange}
                required
                placeholder="e.g., Introduction to Python Programming"
                error={formErrors.title}
                fullWidth
              />
              
              <FormInput
                label="Description"
                name="description"
                id="description"
                value={formData.description}
                onChange={handleChange}
                required
                placeholder="Describe what students will learn in this course"
                multiline
                rows={4}
                error={formErrors.description}
                fullWidth
              />
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label htmlFor="category_id" className="block text-gray-700 font-medium mb-1">
                    Category <span className="text-red-500">*</span>
                  </label>
                  <select
                    id="category_id"
                    name="category_id"
                    value={formData.category_id}
                    onChange={handleChange}
                    required
                    className={`w-full p-2 border rounded-md ${
                      formErrors.category_id ? 'border-red-500' : 'border-gray-300'
                    }`}
                  >
                    <option value="">Select a category</option>
                    {categories.map(cat => (
                      <option key={cat.id} value={cat.id}>{cat.name}</option>
                    ))}
                  </select>
                  {formErrors.category_id && (
                    <p className="text-red-500 text-sm mt-1">{formErrors.category_id}</p>
                  )}
                </div>
                
                <div>
                  <label htmlFor="level" className="block text-gray-700 font-medium mb-1">
                    Level
                  </label>
                  <select
                    id="level"
                    name="level"
                    value={formData.level}
                    onChange={handleChange}
                    className="w-full p-2 border border-gray-300 rounded-md"
                  >
                    <option value="beginner">Beginner</option>
                    <option value="intermediate">Intermediate</option>
                    <option value="advanced">Advanced</option>
                    <option value="all_levels">All Levels</option>
                  </select>
                </div>
                
                <div>
                  <label htmlFor="price" className="block text-gray-700 font-medium mb-1">
                    Price (USD)
                  </label>
                  <input
                    id="price"
                    name="price"
                    type="text"
                    value={formData.price}
                    onChange={handleChange}
                    placeholder="e.g., 29.99 (leave empty for free)"
                    className={`w-full p-2 border rounded-md ${
                      formErrors.price ? 'border-red-500' : 'border-gray-300'
                    }`}
                  />
                  {formErrors.price && (
                    <p className="text-red-500 text-sm mt-1">{formErrors.price}</p>
                  )}
                </div>
                
                <div>
                  <label htmlFor="thumbnail" className="block text-gray-700 font-medium mb-1">
                    Thumbnail Image
                  </label>
                  <input
                    id="thumbnail"
                    type="file"
                    accept="image/*"
                    onChange={handleThumbnailChange}
                    className="w-full p-2 border border-gray-300 rounded-md"
                  />
                  <p className="text-gray-500 text-sm mt-1">
                    Recommended size: 1280×720 pixels
                  </p>
                  
                  {/* Thumbnail preview */}
                  {thumbnailPreview && (
                    <div className="mt-3">
                      <p className="text-gray-700 font-medium mb-1">Preview:</p>
                      <img 
                        src={thumbnailPreview} 
                        alt="Thumbnail preview" 
                        className="w-full h-40 object-cover rounded-md border border-gray-300"
                      />
                    </div>
                  )}
                </div>
              </div>
              
              <div className="flex items-center">
                <input
                  id="has_certificate"
                  name="has_certificate"
                  type="checkbox"
                  checked={formData.has_certificate}
                  onChange={handleChange}
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                />
                <label htmlFor="has_certificate" className="ml-2 text-gray-700">
                  This course offers a completion certificate
                </label>
              </div>
              
              <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200 mt-6">
                <Button 
                  type="button" 
                  variant="outlined" 
                  color="secondary" 
                  onClick={() => navigate('/instructor/dashboard')}
                  disabled={loading}
                >
                  Cancel
                </Button>
                <Button 
                  type="submit" 
                  variant="contained" 
                  color="primary" 
                  loading={loading}
                >
                  {loading ? 'Creating...' : 'Create Course'}
                </Button>
              </div>
            </form>
          </Card>
        </Container>
      </div>
    </MainLayout>
  );
};

export default CreateCoursePage;
// END OF CODE