/**
 * File: frontend/src/pages/instructor/EditCoursePage.jsx
 * Version: 2.1.1
 * Date: 2025-08-01
 * Author: nanthiniSanthanam
 * 
 * Enhanced Course Editor with Improved Course Fetching
 * 
 * Key Improvements:
 * 1. Properly handles slug vs ID-based course fetching
 * 2. Implements intelligent course lookup strategy
 * 3. Includes better error handling and user feedback
 * 4. Adds loading states and graceful fallbacks
 * 5. Fixed button loading state prop format issue
 * 6. Improved FormData handling for file uploads
 * 7. Added better thumbnail preview functionality
 * 8. Fixed parameter extraction to match App.jsx route definitions
 * 
 * This component allows instructors to edit existing courses with:
 * - Form validation
 * - Image upload
 * - Category selection
 * - Level selection
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
// Direct imports to avoid casing issues
import Button from '../../components/common/Button';
import Card from '../../components/common/Card';
import Alert from '../../components/common/Alert';
import FormInput from '../../components/common/FormInput';
import LoadingScreen from '../../components/common/LoadingScreen';
import MainLayout from '../../components/layouts/MainLayout';
import instructorService from '../../services/instructorService';
import api from '../../services/api'; // Fix import to use the correct API object
import { splitToList } from '../../utils/transformData'; // Import this utility or create it
import authPersist from '../../utils/authPersist';

const EditCoursePage = () => {
  // Use courseIdentifier directly to match the route param in App.jsx
  const { courseIdentifier } = useParams();
  const navigate = useNavigate();
  
  const [courseData, setCourseData] = useState({
    title: '',
    subtitle: '',
    description: '',
    category_id: '',
    price: '',
    discount_price: '',
    level: 'all_levels',
    has_certificate: false,
    is_featured: false,
    is_published: false,
    initialPublishState: false,
    requirements: [],
    skills: []
  });

  const [thumbnail, setThumbnail] = useState(null);
  const [thumbnailPreview, setThumbnailPreview] = useState('');
  const [thumbnailLoading, setThumbnailLoading] = useState(false);
  const [categories, setCategories] = useState([]);
  const [categoriesLoading, setCategoriesLoading] = useState(true);
  const [categoriesError, setCategoriesError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [courseSlugState, setCourseSlugState] = useState(null);

  // Fetch course and categories on component mount
  useEffect(() => {
    const fetchCourseAndCategories = async () => {
      try {
        // Validate that we have a course identifier
        if (!courseIdentifier) {
          throw new Error('Course identifier is missing');
        }
        
        // Refresh auth token to prevent session expiration during editing
        if (authPersist && typeof authPersist.isTokenValid === 'function' && 
            typeof authPersist.refreshTokenExpiry === 'function') {
          if (authPersist.isTokenValid()) {
            authPersist.refreshTokenExpiry();
          }
        }

        // Determine if we're using slug or ID
        const isSlug = !Number.isInteger(Number(courseIdentifier));
        let targetCourse;
        
        if (isSlug) {
          // If it's a slug, fetch directly
          console.log(`Fetching course by slug: ${courseIdentifier}`);
          try {
            const response = await instructorService.getCourseBySlug(courseIdentifier);
            targetCourse = response.data || response;
          } catch (error) {
            console.error("Error fetching by slug:", error);
            throw new Error(`Course with slug "${courseIdentifier}" not found`);
          }
        } else {
          // If it's an ID, first get all courses and find the matching one
          console.log(`Fetching course by ID: ${courseIdentifier}`);
          const coursesResponse = await instructorService.getAllCourses();
          const courses = coursesResponse?.results || coursesResponse || [];
          
          // Find the course with matching ID
          targetCourse = courses.find(course => 
            course.id?.toString() === courseIdentifier.toString()
          );
          
          if (!targetCourse) {
            console.error(`Course with ID ${courseIdentifier} not found in courses list`);
            
            // Try direct fetch if ID lookup fails
            try {
              const idResponse = await instructorService.getCourse(courseIdentifier);
              targetCourse = idResponse.data || idResponse;
            } catch (directError) {
              console.error('Direct fetch by ID failed:', directError);
              throw new Error(`Course with ID ${courseIdentifier} not found`);
            }
          } else {
            // If found by ID in list, get full details using slug
            const detailResponse = await instructorService.getCourseBySlug(targetCourse.slug);
            targetCourse = detailResponse.data || detailResponse;
          }
        }
        
        if (!targetCourse) {
          throw new Error(`Course not found with identifier: ${courseIdentifier}`);
        }
        
        // Store the slug for later use
        setCourseSlugState(targetCourse.slug);
        console.log(`Found course slug: ${targetCourse.slug}`);
        
        // Set course data in state
        setCourseData({
          id: targetCourse.id || '',
          title: targetCourse.title || '',
          subtitle: targetCourse.subtitle || '',
          description: targetCourse.description || '',
          category_id: targetCourse.category?.id || '',
          price: targetCourse.price?.toString() || '',
          discount_price: targetCourse.discount_price?.toString() || '',
          level: targetCourse.level || 'all_levels',
          has_certificate: targetCourse.has_certificate || false,
          is_featured: targetCourse.is_featured || false,
          is_published: targetCourse.is_published || false,
          initialPublishState: targetCourse.is_published || false,
          requirements: targetCourse.requirements || [],
          skills: targetCourse.skills || []
        });
        
        // Set thumbnail preview if exists
        if (targetCourse.thumbnail) {
          setThumbnailPreview(targetCourse.thumbnail);
        }
        
        // Fetch categories
        setCategoriesLoading(true);
        try {
          const categoriesResponse = await api.category.getAllCategories();
          setCategories(categoriesResponse || []);
          setCategoriesError(null);
        } catch (catError) {
          console.error('Error fetching categories:', catError);
          setCategoriesError('Failed to load categories');
        } finally {
          setCategoriesLoading(false);
        }
        
      } catch (err) {
        console.error('Error fetching course data:', err);
        setError(`Failed to load course data: ${err.message || 'Unknown error'}`);
      } finally {
        setLoading(false);
      }
    };
    
    fetchCourseAndCategories();
  }, [courseIdentifier]);

  // Handle input changes
  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    
    if (type === 'checkbox') {
      setCourseData(prev => ({ ...prev, [name]: checked }));
    } else {
      setCourseData(prev => ({ ...prev, [name]: value }));
    }
  };

  // Handle thumbnail image upload
  const handleThumbnailChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setThumbnail(file);
      setThumbnailLoading(true);
      
      const reader = new FileReader();
      reader.onloadend = () => {
        setThumbnailPreview(reader.result);
        setThumbnailLoading(false);
      };
      reader.onerror = () => {
        console.error('Error reading file');
        setThumbnailLoading(false);
      };
      reader.readAsDataURL(file);
    }
  };

  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Don't submit if thumbnail is still loading
    if (thumbnailLoading) {
      setError("Please wait for thumbnail to finish loading");
      return;
    }
    
    setSubmitting(true);
    setError(null);
    setSuccess(null);
    
    try {
      if (!courseSlugState) {
        throw new Error('Course slug not found for update');
      }
      
      // Create FormData for multipart submission
      const formData = new FormData();
      
      // Add basic fields
      formData.append('title', courseData.title);
      formData.append('subtitle', courseData.subtitle || '');
      formData.append('description', courseData.description);
      formData.append('category_id', courseData.category_id);
      formData.append('level', courseData.level);
      
      // Handle price fields
      formData.append('price', courseData.price === '' ? '0' : courseData.price);
      if (courseData.discount_price) {
        formData.append('discount_price', courseData.discount_price);
      }
      
      // Handle boolean fields (except is_published - that'll be handled separately)
      formData.append('has_certificate', courseData.has_certificate);
      formData.append('is_featured', courseData.is_featured);
      
      // Handle arrays
      const requirements = Array.isArray(courseData.requirements) 
        ? courseData.requirements 
        : splitToList(courseData.requirements);
        
      const skills = Array.isArray(courseData.skills)
        ? courseData.skills
        : splitToList(courseData.skills);
      
      // Append requirements as JSON
      if (requirements.length > 0) {
        formData.append('requirements', JSON.stringify(requirements));
      }
      
      // Append skills as JSON
      if (skills.length > 0) {
        formData.append('skills', JSON.stringify(skills));
      }
      
      // Add thumbnail if a new one was selected (only if it's a File object)
      if (thumbnail instanceof File) {
        formData.append('thumbnail', thumbnail);
      }
      
      // Update course using the slug
      const updatedCourse = await instructorService.updateCourse(courseSlugState, formData);
      
      // Handle publishing state separately using the dedicated endpoint
      const wasPublished = courseData.initialPublishState;
      const shouldBePublished = courseData.is_published;
      
      if (wasPublished !== shouldBePublished) {
        await instructorService.publishCourse(courseSlugState, shouldBePublished);
      }
      
      setSuccess('Course updated successfully!');
      
      // Navigate after a short delay
      setTimeout(() => {
        // Navigate to course page instead of dashboard
        navigate(`/courses/${courseSlugState}`);
      }, 2000);
    } catch (err) {
      console.error('Error updating course:', err);
      
      // Format error message
      let errorMessage = 'Failed to update course';
      
      if (err.details) {
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
      
      setError(`Failed to update course: ${errorMessage}`);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return <MainLayout><LoadingScreen message="Loading course data..." /></MainLayout>;
  }

  return (
    <MainLayout>
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold mb-6">Edit Course</h1>
        
        {error && (
          <Alert type="error" className="mb-6">
            {error}
          </Alert>
        )}
        
        {success && (
          <Alert type="success" className="mb-6">
            {success}
          </Alert>
        )}
        
        <Card className="p-6">
          <form onSubmit={handleSubmit} encType="multipart/form-data">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="md:col-span-2">
                <FormInput
                  label="Course Title"
                  name="title"
                  value={courseData.title}
                  onChange={handleChange}
                  required
                  fullWidth
                />
              </div>
              
              <div className="md:col-span-2">
                <FormInput
                  label="Subtitle"
                  name="subtitle"
                  value={courseData.subtitle}
                  onChange={handleChange}
                  fullWidth
                />
              </div>
              
              <div className="md:col-span-2">
                <FormInput
                  label="Description"
                  name="description"
                  value={courseData.description}
                  onChange={handleChange}
                  multiline
                  rows={6}
                  required
                  fullWidth
                />
              </div>
              
              <div>
                <FormInput
                  label="Category"
                  name="category_id"
                  value={courseData.category_id}
                  onChange={handleChange}
                  select
                  required
                  fullWidth
                >
                  <option value="">Select a category</option>
                  {categories.map(category => (
                    <option key={category.id} value={category.id}>
                      {category.name}
                    </option>
                  ))}
                </FormInput>
              </div>
              
              <div>
                <FormInput
                  label="Level"
                  name="level"
                  value={courseData.level}
                  onChange={handleChange}
                  select
                  required
                  fullWidth
                >
                  <option value="beginner">Beginner</option>
                  <option value="intermediate">Intermediate</option>
                  <option value="advanced">Advanced</option>
                  <option value="all_levels">All Levels</option>
                </FormInput>
              </div>
              
              <div>
                <FormInput
                  label="Price ($)"
                  name="price"
                  type="number"
                  value={courseData.price}
                  onChange={handleChange}
                  required
                  fullWidth
                />
              </div>
              
              <div>
                <FormInput
                  label="Discount Price ($)"
                  name="discount_price"
                  type="number"
                  value={courseData.discount_price}
                  onChange={handleChange}
                  fullWidth
                />
              </div>
              
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Thumbnail Image
                </label>
                
                <div className="flex items-center space-x-4">
                  {thumbnailPreview && (
                    <div className="relative w-32 h-32 overflow-hidden rounded-md">
                      <img 
                        src={thumbnailPreview} 
                        alt="Course thumbnail" 
                        className="object-cover w-full h-full"
                      />
                    </div>
                  )}
                  
                  <input
                    type="file"
                    accept="image/*"
                    onChange={handleThumbnailChange}
                    className="block w-full text-sm text-gray-500
                      file:mr-4 file:py-2 file:px-4
                      file:rounded-full file:border-0
                      file:text-sm file:font-semibold
                      file:bg-violet-50 file:text-violet-700
                      hover:file:bg-violet-100"
                  />
                </div>
              </div>
              
              <div className="md:col-span-2">
                <FormInput
                  label="Course Requirements (One per line)"
                  name="requirements"
                  value={Array.isArray(courseData.requirements) ? courseData.requirements.join('\n') : courseData.requirements}
                  onChange={handleChange}
                  multiline
                  rows={4}
                  fullWidth
                />
              </div>
              
              <div className="md:col-span-2">
                <FormInput
                  label="Skills Students Will Learn (One per line)"
                  name="skills"
                  value={Array.isArray(courseData.skills) ? courseData.skills.join('\n') : courseData.skills}
                  onChange={handleChange}
                  multiline
                  rows={4}
                  fullWidth
                />
              </div>
              
              <div className="flex items-center space-x-4">
                <label className="inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    name="has_certificate"
                    checked={courseData.has_certificate}
                    onChange={handleChange}
                    className="form-checkbox h-5 w-5 text-primary-600"
                  />
                  <span className="ml-2 text-sm text-gray-700">
                    Has Certificate
                  </span>
                </label>
                
                <label className="inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    name="is_featured"
                    checked={courseData.is_featured}
                    onChange={handleChange}
                    className="form-checkbox h-5 w-5 text-primary-600"
                  />
                  <span className="ml-2 text-sm text-gray-700">
                    Featured Course
                  </span>
                </label>
                
                <label className="inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    name="is_published"
                    checked={courseData.is_published}
                    onChange={handleChange}
                    className="form-checkbox h-5 w-5 text-primary-600"
                  />
                  <span className="ml-2 text-sm text-gray-700">
                    Published
                  </span>
                </label>
              </div>
              
              <div className="md:col-span-2 flex justify-end space-x-4 mt-6">
                <Button
                  type="button"
                  variant="outlined"
                  color="secondary"
                  onClick={() => navigate(`/instructor/dashboard`)}
                  disabled={submitting}
                >
                  Cancel
                </Button>
                
                <Button
                  type="submit"
                  variant="contained"
                  color="primary"
                  loading={submitting ? true : undefined}
                >
                  {submitting ? 'Updating...' : 'Update Course'}
                </Button>
              </div>
            </div>
          </form>
        </Card>
      </div>
    </MainLayout>
  );
};

export default EditCoursePage;
// END OF CODE