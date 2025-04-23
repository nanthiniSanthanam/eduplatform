import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import api from '../services/api';

const CourseDetailPage = () => {
  const { courseId } = useParams();
  const navigate = useNavigate();
  const { currentUser } = useAuth();
  const [course, setCourse] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [isEnrolled, setIsEnrolled] = useState(false);
  const [enrolling, setEnrolling] = useState(false);
  const [expandedModules, setExpandedModules] = useState({});
  
  // Convert the current UTC date string to a Date object
  const currentDate = new Date('2025-04-20T09:26:55Z');

  useEffect(() => {
    const fetchCourse = async () => {
      try {
        setLoading(true);
        
        // Simulate API call delay
        await new Promise(resolve => setTimeout(resolve, 800));
        
        // In a real application, this would be:
        // const response = await api.get(`/api/courses/${courseId}/`);
        // setCourse(response.data);
        
        // Mock course data for demonstration
        const mockCourse = {
          id: parseInt(courseId),
          title: 'Advanced React and Redux: Building Scalable Web Applications',
          description: 'Take your React skills to the next level with this comprehensive course on advanced React patterns, Redux state management, and building scalable web applications. You\'ll learn how to architect complex React applications, implement efficient state management with Redux and Redux Toolkit, optimize performance, and deploy your applications to production.',
          long_description: `
            <p>React has become the most popular framework for building modern web applications, but mastering its advanced concepts and patterns can be challenging. This course is designed to take developers who already have basic React knowledge to an advanced level where they can confidently build and scale complex applications.</p>
            
            <p>You'll learn directly from an industry expert with over 10 years of experience building production React applications for Fortune 500 companies. Throughout this course, we'll build a real-world project from scratch, implementing best practices and exploring advanced concepts along the way.</p>

            <p>By the end of this course, you'll have a deep understanding of React's component model, state management with Redux, performance optimization techniques, and deployment strategies. You'll be equipped with the knowledge and practical experience to build efficient, maintainable React applications at scale.</p>
          `,
          instructor: {
            name: 'Alex Johnson',
            bio: 'Senior Software Engineer with 10+ years of experience specializing in React and frontend architecture. Previously worked at Facebook, Google, and several successful startups.',
            profile_picture: 'https://images.unsplash.com/photo-1531427186611-ecfd6d936c79?ixlib=rb-1.2.1&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=facearea&facepad=2&w=256&h=256&q=80'
          },
          category: { id: 1, name: 'Web Development' },
          thumbnail: 'https://images.unsplash.com/photo-1633356122544-f134324a6cee?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1170&q=80',
          cover_image: 'https://images.unsplash.com/photo-1587620962725-abab7fe55159?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1170&q=80',
          is_premium: true,
          price: 79.99,
          sale_price: 49.99,
          sale_end_date: '2025-05-15T23:59:59Z',
          rating: 4.8,
          enrolled_count: 2450,
          duration: '32 hours',
          last_updated: '2025-03-25',
          language: 'English',
          certificate: true,
          level: 'Advanced',
          prerequisites: [
            'Basic knowledge of React and JavaScript',
            'Familiarity with ES6+ syntax',
            'Understanding of component-based architecture',
            'Experience with npm and node.js'
          ],
          what_you_will_learn: [
            'Master advanced React patterns including Hooks, Context API, and Suspense',
            'Implement efficient state management with Redux and Redux Toolkit',
            'Build reusable component libraries with styled-components',
            'Optimize React performance with code splitting and lazy loading',
            'Set up automated testing with Jest and React Testing Library',
            'Implement authentication and authorization in React applications',
            'Create responsive interfaces that work across all devices',
            'Deploy React applications to production using modern CI/CD pipelines'
          ],
          modules: [
            {
              id: 1,
              title: 'Introduction and Setup',
              description: 'Get your development environment ready and understand the course structure.',
              lessons: [
                { id: 101, title: 'Course Overview and Goals', is_free: true, duration: '10 min' },
                { id: 102, title: 'Setting Up Your Development Environment', is_free: true, duration: '15 min' },
                { id: 103, title: 'Project Overview and Architecture', is_free: true, duration: '20 min' },
                { id: 104, title: 'Modern JavaScript Features Review', is_free: false, duration: '25 min' }
              ]
            },
            {
              id: 2,
              title: 'Advanced React Concepts',
              description: 'Deep dive into React\'s more advanced features and patterns.',
              lessons: [
                { id: 201, title: 'Understanding React\'s Component Lifecycle', is_free: false, duration: '30 min' },
                { id: 202, title: 'Advanced Hooks: useCallback, useMemo, useRef', is_free: false, duration: '45 min' },
                { id: 203, title: 'Custom Hooks: Creating Reusable Logic', is_free: false, duration: '40 min' },
                { id: 204, title: 'Context API for State Management', is_free: false, duration: '35 min' },
                { id: 205, title: 'Error Boundaries and Fallback UI', is_free: false, duration: '25 min' }
              ]
            },
            {
              id: 3,
              title: 'Redux State Management',
              description: 'Learn to manage complex application state with Redux.',
              lessons: [
                { id: 301, title: 'Redux Core Concepts', is_free: false, duration: '40 min' },
                { id: 302, title: 'Setting Up Redux with React', is_free: false, duration: '30 min' },
                { id: 303, title: 'Redux Toolkit: Simplifying Redux', is_free: false, duration: '45 min' },
                { id: 304, title: 'Middleware and Async Operations with Redux', is_free: false, duration: '50 min' },
                { id: 305, title: 'Redux DevTools and Debugging', is_free: false, duration: '25 min' }
              ]
            },
            {
              id: 4,
              title: 'Styling in React',
              description: 'Implement modern styling approaches in React applications.',
              lessons: [
                { id: 401, title: 'CSS-in-JS with Styled Components', is_free: false, duration: '35 min' },
                { id: 402, title: 'Theme Systems and Dark Mode', is_free: false, duration: '40 min' },
                { id: 403, title: 'Responsive Design in React', is_free: false, duration: '30 min' },
                { id: 404, title: 'Animation in React Applications', is_free: false, duration: '45 min' }
              ]
            },
            {
              id: 5,
              title: 'Performance Optimization',
              description: 'Learn techniques to make your React applications blazing fast.',
              lessons: [
                { id: 501, title: 'Identifying Performance Bottlenecks', is_free: false, duration: '25 min' },
                { id: 502, title: 'Memoization Techniques', is_free: false, duration: '35 min' },
                { id: 503, title: 'Code Splitting and Lazy Loading', is_free: false, duration: '30 min' },
                { id: 504, title: 'Virtual List and Windowing', is_free: false, duration: '40 min' },
                { id: 505, title: 'Server-side Rendering for Performance', is_free: false, duration: '45 min' }
              ]
            },
            {
              id: 6,
              title: 'Testing React Applications',
              description: 'Implement robust testing strategies for your React code.',
              lessons: [
                { id: 601, title: 'Testing Philosophy and Setup', is_free: false, duration: '20 min' },
                { id: 602, title: 'Unit Testing with Jest', is_free: false, duration: '40 min' },
                { id: 603, title: 'Component Testing with React Testing Library', is_free: false, duration: '45 min' },
                { id: 604, title: 'Integration Testing', is_free: false, duration: '30 min' },
                { id: 605, title: 'E2E Testing with Cypress', is_free: false, duration: '50 min' }
              ]
            },
            {
              id: 7,
              title: 'Deployment and CI/CD',
              description: 'Learn to deploy React applications to production environments.',
              lessons: [
                { id: 701, title: 'Build Optimization', is_free: false, duration: '25 min' },
                { id: 702, title: 'Deployment Options', is_free: false, duration: '30 min' },
                { id: 703, title: 'Setting Up CI/CD with GitHub Actions', is_free: false, duration: '45 min' },
                { id: 704, title: 'Monitoring and Error Tracking', is_free: false, duration: '35 min' },
                { id: 705, title: 'Course Conclusion and Next Steps', is_free: false, duration: '15 min' }
              ]
            }
          ],
          reviews: [
            {
              id: 1,
              user: 'Sarah Chen',
              avatar: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?ixlib=rb-1.2.1&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=facearea&facepad=2&w=100&h=100&q=80',
              rating: 5,
              comment: 'This course completely transformed how I build React applications. The instructor explains complex concepts clearly and the projects helped cement my understanding. Highly recommended!',
              date: '2025-04-10'
            },
            {
              id: 2,
              user: 'Michael Rodriguez',
              avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?ixlib=rb-1.2.1&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=facearea&facepad=2&w=100&h=100&q=80',
              rating: 4,
              comment: 'Great content with lots of practical examples. Some sections could have more exercises, but overall it\'s an excellent course for advancing your React skills.',
              date: '2025-03-25'
            },
            {
              id: 3,
              user: 'Lisa Washington',
              avatar: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?ixlib=rb-1.2.1&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=facearea&facepad=2&w=100&h=100&q=80',
              rating: 5,
              comment: 'Alex is an amazing teacher! His explanations of complex Redux patterns made things click that I\'ve been struggling with for months. The section on performance optimization was particularly valuable for my work.',
              date: '2025-04-02'
            },
            {
              id: 4,
              user: 'David Kim',
              avatar: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?ixlib=rb-1.2.1&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=facearea&facepad=2&w=100&h=100&q=80',
              rating: 5,
              comment: 'I\'ve taken several React courses before, but this one truly delivers on the "advanced" promise. The real-world examples and project-based approach helped me improve my code quality significantly.',
              date: '2025-03-18'
            }
          ],
          faqs: [
            {
              question: 'Is this course right for beginners?',
              answer: 'This course is designed for developers who already have a basic understanding of React. If you\'re new to React, we recommend starting with our "React Fundamentals" course first.'
            },
            {
              question: 'Will I receive a certificate upon completion?',
              answer: 'Yes, you will receive a certificate of completion that you can share on your resume or LinkedIn profile.'
            },
            {
              question: 'How long do I have access to the course?',
              answer: 'Once enrolled, you have lifetime access to the course content, including all future updates.'
            },
            {
              question: 'Are there any projects included in this course?',
              answer: 'Yes, you\'ll build a complete full-stack application throughout the course, implementing all the concepts you learn in a practical, real-world project.'
            },
            {
              question: 'Is there any support if I have questions?',
              answer: 'Absolutely! You\'ll have access to our community forum where you can ask questions and get help from the instructor and other students.'
            }
          ]
        };
        
        setCourse(mockCourse);
        
        // Check if user is enrolled
        // In a real application, this would be an API call
        if (currentUser) {
          // Simulate API call to check enrollment status
          await new Promise(resolve => setTimeout(resolve, 200));
          // For demo purposes, we'll randomly determine enrollment status
          setIsEnrolled(Math.random() > 0.5);
        } else {
          setIsEnrolled(false);
        }
        
      } catch (err) {
        console.error('Error fetching course:', err);
        setError('Failed to load course details. Please try again.');
      } finally {
        setLoading(false);
      }
    };
    
    fetchCourse();
  }, [courseId, currentUser]);

  const handleEnroll = async () => {
    if (!currentUser) {
      // Redirect to login with return path
      navigate('/login', { state: { from: `/courses/${courseId}` } });
      return;
    }

    try {
      setEnrolling(true);
      
      // In a real app, this would be an API call
      // await api.post(`/api/courses/${courseId}/enroll/`);
      
      // Simulate API call delay
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setIsEnrolled(true);
      // Show success message or redirect to course content
      
    } catch (err) {
      console.error('Error enrolling in course:', err);
      alert('Failed to enroll in course. Please try again.');
    } finally {
      setEnrolling(false);
    }
  };

  const toggleModule = (moduleId) => {
    setExpandedModules(prev => ({
      ...prev,
      [moduleId]: !prev[moduleId]
    }));
  };

  const calculateTotalLessons = () => {
    return course?.modules.reduce((total, module) => total + module.lessons.length, 0) || 0;
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (error || !course) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="bg-red-50 border-l-4 border-red-500 p-4 rounded-md">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-700">{error || 'Course not found'}</p>
              <Link to="/courses" className="text-sm font-medium text-red-700 hover:text-red-600 underline">
                Return to courses
              </Link>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Check if the course has a sale and if it's still valid
  const saleEndDate = new Date(course.sale_end_date);
  const isSaleActive = course.sale_price && saleEndDate > currentDate;
  
  // Calculate time remaining for sale
  let timeRemaining = null;
  if (isSaleActive) {
    const diffTime = saleEndDate - currentDate;
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
    const diffHours = Math.floor((diffTime % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    
    if (diffDays > 0) {
      timeRemaining = `${diffDays} day${diffDays > 1 ? 's' : ''} ${diffHours} hour${diffHours > 1 ? 's' : ''}`;
    } else {
      timeRemaining = `${diffHours} hour${diffHours > 1 ? 's' : ''}`;
    }
  }

  return (
    <div className="bg-gray-50">
      {/* Hero Section */}
      <div className="bg-gray-900 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <div className="lg:grid lg:grid-cols-2 lg:gap-8 items-center">
            <div>
              <div className="flex items-center space-x-2">
                <Link to="/courses" className="text-primary-300 hover:text-primary-200 text-sm font-medium flex items-center">
                  <svg className="h-4 w-4 mr-1" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                  </svg>
                  Back to Courses
                </Link>
                <span className="text-gray-400">/</span>
                <span className="text-primary-300 text-sm font-medium">{course.category.name}</span>
              </div>
              
              <h1 className="mt-4 text-3xl font-extrabold text-white sm:text-4xl">
                {course.title}
              </h1>
              
              <p className="mt-4 text-lg text-gray-300">
                {course.description}
              </p>
              
              <div className="mt-6 flex items-center">
                <img 
                  className="h-10 w-10 rounded-full"
                  src={course.instructor.profile_picture}
                  alt={course.instructor.name}
                />
                <div className="ml-3">
                  <p className="text-sm font-medium text-white">
                    {course.instructor.name}
                  </p>
                  <p className="text-xs text-gray-400">
                    Instructor
                  </p>
                </div>
              </div>
              
              <div className="mt-6 flex flex-wrap items-center text-sm text-gray-300 gap-y-2">
                <div className="flex items-center mr-6">
                  <svg className="h-5 w-5 mr-1 text-primary-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  {course.duration}
                </div>
                <div className="flex items-center mr-6">
                  <svg className="h-5 w-5 mr-1 text-primary-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                  </svg>
                  {calculateTotalLessons()} lessons
                </div>
                <div className="flex items-center mr-6">
                  <svg className="h-5 w-5 mr-1 text-primary-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                  {course.level} level
                </div>
                <div className="flex items-center mr-6">
                  <svg className="h-5 w-5 mr-1 text-primary-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
                  </svg>
                  {course.language}
                </div>
                <div className="flex items-center">
                  <svg className="h-5 w-5 mr-1 text-primary-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                  Last updated: {new Date(course.last_updated).toLocaleDateString()}
                </div>
              </div>
              
              <div className="mt-6 flex items-center">
                <div className="flex items-center">
                  {[0, 1, 2, 3, 4].map((rating) => (
                    <svg 
                      key={rating} 
                      className={`h-5 w-5 ${rating < Math.floor(course.rating) ? 'text-yellow-400' : 'text-gray-500'}`}
                      xmlns="http://www.w3.org/2000/svg" 
                      viewBox="0 0 20 20" 
                      fill="currentColor"
                    >
                      <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                    </svg>
                  ))}
                </div>
                <p className="ml-2 text-sm text-gray-300">
                  {course.rating} ({course.enrolled_count.toLocaleString()} students)
                </p>
              </div>
            </div>
            
            <div className="mt-12 lg:mt-0">
              <div className="relative">
                <img 
                  src={course.cover_image} 
                  alt={course.title} 
                  className="rounded-lg shadow-xl"
                />
                <div className="absolute inset-0 flex items-center justify-center">
                  <button 
                    className="bg-primary-600 hover:bg-primary-700 text-white rounded-full p-4 flex items-center justify-center shadow-lg transform transition-transform hover:scale-110"
                    aria-label="Play preview"
                  >
                    <svg className="h-8 w-8" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="lg:grid lg:grid-cols-3 lg:gap-8">
          {/* Left Content (2/3 width) */}
          <div className="lg:col-span-2">
            {/* Tabs */}
            <div className="border-b border-gray-200 mb-8">
              <div className="flex -mb-px overflow-x-auto">
                {['overview', 'curriculum', 'instructor', 'reviews', 'faq'].map((tab) => (
                  <button
                    key={tab}
                    onClick={() => setActiveTab(tab)}
                    className={`${
                      activeTab === tab
                        ? 'border-primary-500 text-primary-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    } whitespace-nowrap py-4 px-6 border-b-2 font-medium text-sm capitalize`}
                  >
                    {tab}
                  </button>
                ))}
              </div>
            </div>

            {/* Tab Content */}
            <div>
              {activeTab === 'overview' && (
                <div>
                  <h2 className="text-2xl font-bold text-gray-900 mb-6">About This Course</h2>
                  
                  <div 
                    className="prose prose-lg max-w-none text-gray-700"
                    dangerouslySetInnerHTML={{ __html: course.long_description }}  
                  ></div>
                  
                  <div className="mt-10">
                    <h3 className="text-xl font-bold text-gray-900 mb-4">What You'll Learn</h3>
                    <ul className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {course.what_you_will_learn.map((item, index) => (
                        <li key={index} className="flex items-start">
                          <svg className="h-5 w-5 text-green-500 flex-shrink-0 mr-2 mt-0.5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                          </svg>
                          <span className="text-gray-700">{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                  
                  <div className="mt-10">
                    <h3 className="text-xl font-bold text-gray-900 mb-4">Prerequisites</h3>
                    <ul className="space-y-2">
                      {course.prerequisites.map((item, index) => (
                        <li key={index} className="flex items-start">
                          <svg className="h-5 w-5 text-primary-500 flex-shrink-0 mr-2 mt-0.5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          <span className="text-gray-700">{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}

              {activeTab === 'curriculum' && (
                <div>
                  <div className="flex items-center justify-between mb-6">
                    <h2 className="text-2xl font-bold text-gray-900">Course Content</h2>
                    <div className="text-sm text-gray-600">
                      {course.modules.length} modules • {calculateTotalLessons()} lessons • {course.duration} total length
                    </div>
                  </div>
                  
                  <div className="space-y-4">
                    {course.modules.map((module) => (
                      <div key={module.id} className="bg-white shadow overflow-hidden rounded-md border border-gray-200">
                        <div 
                          className="px-4 py-5 cursor-pointer flex justify-between items-center hover:bg-gray-50"
                          onClick={() => toggleModule(module.id)}
                        >
                          <div className="flex items-center">
                            <svg 
                              className={`h-5 w-5 text-gray-500 transform ${expandedModules[module.id] ? 'rotate-90' : ''} transition-transform`}
                              xmlns="http://www.w3.org/2000/svg" 
                              viewBox="0 0 20 20" 
                              fill="currentColor"
                            >
                              <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                            </svg>
                            <div className="ml-3">
                              <h3 className="text-lg font-medium text-gray-900">{module.title}</h3>
                              <p className="text-sm text-gray-500">{module.description}</p>
                            </div>
                          </div>
                          <div className="text-sm text-gray-500">
                            {module.lessons.length} lessons
                          </div>
                        </div>
                        
                        {expandedModules[module.id] && (
                          <div className="border-t border-gray-200 divide-y divide-gray-200">
                            {module.lessons.map((lesson) => (
                              <div key={lesson.id} className="px-4 py-4 flex justify-between items-center">
                                <div className="flex items-center">
                                  {lesson.is_free ? (
                                    <svg className="h-5 w-5 text-primary-500 mr-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                    </svg>
                                  ) : (
                                    <svg className="h-5 w-5 text-gray-400 mr-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                                    </svg>
                                  )}
                                  <span className="text-sm font-medium text-gray-900">{lesson.title}</span>
                                  {lesson.is_free && (
                                    <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                                      Free Preview
                                    </span>
                                  )}
                                </div>
                                <div className="flex items-center text-sm text-gray-500">
                                  <svg className="h-4 w-4 mr-1" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                                  </svg>
                                  {lesson.duration}
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {activeTab === 'instructor' && (
                <div>
                  <h2 className="text-2xl font-bold text-gray-900 mb-6">About the Instructor</h2>
                  
                  <div className="flex items-center mb-6">
                    <img 
                      className="h-16 w-16 rounded-full"
                      src={course.instructor.profile_picture}
                      alt={course.instructor.name}
                    />
                    <div className="ml-4">
                      <h3 className="text-xl font-medium text-gray-900">{course.instructor.name}</h3>
                      <p className="text-gray-500">Professional Instructor</p>
                    </div>
                  </div>
                  
                  <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
                    <div className="flex space-x-6 mb-6">
                      <div className="text-center">
                        <div className="text-2xl font-bold text-gray-900">15+</div>
                        <div className="text-sm text-gray-500">Courses</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-gray-900">50K+</div>
                        <div className="text-sm text-gray-500">Students</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-gray-900">4.8</div>
                        <div className="text-sm text-gray-500">Average Rating</div>
                      </div>
                    </div>
                    
                    <p className="text-gray-700">
                      {course.instructor.bio}
                    </p>
                    
                    <div className="mt-6 flex space-x-4">
                      <a href="#" className="text-primary-600 hover:text-primary-800 flex items-center">
                        <svg className="h-5 w-5 mr-1" fill="currentColor" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
                          <path d="M19.615 3.184c-3.604-.246-11.631-.245-15.23 0-3.897.266-4.356 2.62-4.385 8.816.029 6.185.484 8.549 4.385 8.816 3.6.245 11.626.246 15.23 0 3.897-.266 4.356-2.62 4.385-8.816-.029-6.185-.484-8.549-4.385-8.816zm-10.615 12.816v-8l8 3.993-8 4.007z"/>
                        </svg>
                        YouTube
                      </a>
                      <a href="#" className="text-primary-600 hover:text-primary-800 flex items-center">
                        <svg className="h-5 w-5 mr-1" fill="currentColor" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
                          <path d="M24 4.557c-.883.392-1.832.656-2.828.775 1.017-.609 1.798-1.574 2.165-2.724-.951.564-2.005.974-3.127 1.195-.897-.957-2.178-1.555-3.594-1.555-3.179 0-5.515 2.966-4.797 6.045-4.091-.205-7.719-2.165-10.148-5.144-1.29 2.213-.669 5.108 1.523 6.574-.806-.026-1.566-.247-2.229-.616-.054 2.281 1.581 4.415 3.949 4.89-.693.188-1.452.232-2.224.084.626 1.956 2.444 3.379 4.6 3.419-2.07 1.623-4.678 2.348-7.29 2.04 2.179 1.397 4.768 2.212 7.548 2.212 9.142 0 14.307-7.721 13.995-14.646.962-.695 1.797-1.562 2.457-2.549z"/>
                        </svg>
                        Twitter
                      </a>
                      <a href="#" className="text-primary-600 hover:text-primary-800 flex items-center">
                        <svg className="h-5 w-5 mr-1" fill="currentColor" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
                          <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/>
                        </svg>
                        Instagram
                      </a>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'reviews' && (
                <div>
                  <div className="flex items-center justify-between mb-6">
                    <h2 className="text-2xl font-bold text-gray-900">Student Reviews</h2>
                    <div className="flex items-center">
                      <div className="flex items-center">
                        {[0, 1, 2, 3, 4].map((rating) => (
                          <svg 
                            key={rating} 
                            className={`h-5 w-5 ${rating < Math.floor(course.rating) ? 'text-yellow-400' : 'text-gray-300'}`}
                            xmlns="http://www.w3.org/2000/svg" 
                            viewBox="0 0 20 20" 
                            fill="currentColor"
                          >
                            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                          </svg>
                        ))}
                      </div>
                      <p className="ml-2 text-gray-900 font-medium">{course.rating}</p>
                      <span className="mx-1.5 text-gray-500">•</span>
                      <p className="text-gray-500">{course.reviews.length} reviews</p>
                    </div>
                  </div>
                  
                  <div className="space-y-6">
                    {course.reviews.map((review) => (
                      <div key={review.id} className="bg-white rounded-lg shadow p-6 border border-gray-200">
                        <div className="flex items-start">
                          <img 
                            className="h-10 w-10 rounded-full"
                            src={review.avatar}
                            alt={review.user}
                          />
                          <div className="ml-4 flex-1">
                            <div className="flex items-center justify-between">
                              <h4 className="text-sm font-medium text-gray-900">{review.user}</h4>
                              <p className="text-xs text-gray-500">{review.date}</p>
                            </div>
                            <div className="mt-1 flex items-center">
                              {[0, 1, 2, 3, 4].map((rating) => (
                                <svg 
                                  key={rating} 
                                  className={`h-4 w-4 ${rating < review.rating ? 'text-yellow-400' : 'text-gray-300'}`}
                                  xmlns="http://www.w3.org/2000/svg" 
                                  viewBox="0 0 20 20" 
                                  fill="currentColor"
                                >
                                  <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                                </svg>
                              ))}
                            </div>
                            <p className="mt-3 text-sm text-gray-700">{review.comment}</p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                  
                  {course.reviews.length > 4 && (
                    <div className="mt-6 text-center">
                      <button className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500">
                        Load More Reviews
                      </button>
                    </div>
                  )}
                </div>
              )}

              {activeTab === 'faq' && (
                <div>
                  <h2 className="text-2xl font-bold text-gray-900 mb-6">Frequently Asked Questions</h2>
                  
                  <dl className="space-y-6 divide-y divide-gray-200">
                    {course.faqs.map((faq, index) => (
                      <div key={index} className="pt-6">
                        <dt className="text-lg font-medium text-gray-900">
                          {faq.question}
                        </dt>
                        <dd className="mt-2 text-base text-gray-700">
                          {faq.answer}
                        </dd>
                      </div>
                    ))}
                  </dl>
                  
                  <div className="mt-10 bg-gray-50 rounded-lg p-6 border border-gray-200">
                    <h3 className="text-lg font-medium text-gray-900">Still have questions?</h3>
                    <p className="mt-1 text-gray-600">If you can't find the answer to your question, feel free to contact us.</p>
                    <div className="mt-4">
                      <button className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500">
                        Contact Support
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Right Sidebar (1/3 width) */}
          <div className="mt-10 lg:mt-0">
            <div className="bg-white rounded-lg shadow-lg border border-gray-200 sticky top-8">
              <div className="p-6">
                {/* Course Video Preview */}
                <div className="relative pb-2/3 mb-6">
                  <img 
                    className="rounded-lg w-full h-40 object-cover"
                    src={course.thumbnail} 
                    alt={course.title} 
                  />
                  <div className="absolute inset-0 flex items-center justify-center">
                    <button 
                      className="bg-primary-600 hover:bg-primary-700 text-white rounded-full p-3 flex items-center justify-center shadow-lg transform transition-transform hover:scale-110"
                      aria-label="Play preview"
                    >
                      <svg className="h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </button>
                  </div>
                </div>
                
                {/* Course Price */}
                {course.is_premium ? (
                  <div className="mb-6">
                    <div className="flex items-center justify-between">
                      {isSaleActive ? (
                        <>
                          <div>
                            <p className="text-3xl font-bold text-gray-900">${course.sale_price.toFixed(2)}</p>
                            <p className="text-sm line-through text-gray-500">${course.price.toFixed(2)}</p>
                          </div>
                          <div className="bg-red-100 text-red-800 px-3 py-1 rounded-md text-sm font-medium">
                            {Math.round((1 - course.sale_price / course.price) * 100)}% off
                          </div>
                        </>
                      ) : (
                        <p className="text-3xl font-bold text-gray-900">${course.price.toFixed(2)}</p>
                      )}
                    </div>
                    
                    {isSaleActive && (
                      <div className="mt-2">
                        <p className="text-sm text-gray-600 flex items-center">
                          <svg className="h-4 w-4 text-red-500 mr-1" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          Sale ends in <span className="font-medium ml-1">{timeRemaining}</span>
                        </p>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="mb-6">
                    <p className="text-3xl font-bold text-green-600">Free</p>
                  </div>
                )}
                
                {/* Call to Action Button */}
                {isEnrolled ? (
                  <button 
                    className="w-full inline-flex justify-center items-center px-5 py-3 border border-transparent text-base font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 mb-4"
                  >
                    <svg className="h-5 w-5 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                    </svg>
                    Continue Learning
                  </button>
                ) : (
                  <button 
                    onClick={handleEnroll}
                    disabled={enrolling}
                    className="w-full inline-flex justify-center items-center px-5 py-3 border border-transparent text-base font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 mb-4"
                  >
                    {enrolling ? (
                      <>
                        <svg className="animate-spin -ml-1 mr-2 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Processing...
                      </>
                    ) : (
                      <>
                        <svg className="h-5 w-5 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" />
                        </svg>
                        Enroll Now
                      </>
                    )}
                  </button>
                )}
                
                <button className="w-full inline-flex justify-center items-center px-5 py-3 border border-gray-300 shadow-sm text-base font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 mb-6">
                  <svg className="h-5 w-5 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                  </svg>
                  Add to Wishlist
                </button>
                
                {/* Course Includes */}
                <div className="border-t border-gray-200 pt-6">
                  <h3 className="text-sm font-medium text-gray-900">This course includes:</h3>
                  <ul className="mt-4 space-y-3">
                    <li className="flex items-start">
                      <svg className="h-5 w-5 text-green-500 mr-2 flex-shrink-0" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <span className="text-sm text-gray-600">{course.duration} of video content</span>
                    </li>
                    <li className="flex items-start">
                      <svg className="h-5 w-5 text-green-500 mr-2 flex-shrink-0" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <span className="text-sm text-gray-600">{calculateTotalLessons()} lessons</span>
                    </li>
                    <li className="flex items-start">
                      <svg className="h-5 w-5 text-green-500 mr-2 flex-shrink-0" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <span className="text-sm text-gray-600">Full lifetime access</span>
                    </li>
                    <li className="flex items-start">
                      <svg className="h-5 w-5 text-green-500 mr-2 flex-shrink-0" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <span className="text-sm text-gray-600">Access on mobile and desktop</span>
                    </li>
                    {course.certificate && (
                      <li className="flex items-start">
                        <svg className="h-5 w-5 text-green-500 mr-2 flex-shrink-0" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <span className="text-sm text-gray-600">Certificate of completion</span>
                      </li>
                    )}
                  </ul>
                </div>
                
                {/* Share Course */}
                <div className="border-t border-gray-200 pt-6 mt-6">
                  <h3 className="text-sm font-medium text-gray-900">Share this course</h3>
                  <div className="mt-4 flex space-x-4">
                    <a href="#" className="text-gray-400 hover:text-gray-500">
                      <span className="sr-only">Facebook</span>
                      <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
                        <path fillRule="evenodd" d="M22 12c0-5.523-4.477-10-10-10S2 6.477 2 12c0 4.991 3.657 9.128 8.438 9.878v-6.987h-2.54V12h2.54V9.797c0-2.506 1.492-3.89 3.777-3.89 1.094 0 2.238.195 2.238.195v2.46h-1.26c-1.243 0-1.63.771-1.63 1.562V12h2.773l-.443 2.89h-2.33v6.988C18.343 21.128 22 16.991 22 12z" clipRule="evenodd" />
                      </svg>
                    </a>
                    <a href="#" className="text-gray-400 hover:text-gray-500">
                      <span className="sr-only">Twitter</span>
                      <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M8.29 20.251c7.547 0 11.675-6.253 11.675-11.675 0-.178 0-.355-.012-.53A8.348 8.348 0 0022 5.92a8.19 8.19 0 01-2.357.646 4.118 4.118 0 001.804-2.27 8.224 8.224 0 01-2.605.996 4.107 4.107 0 00-6.993 3.743 11.65 11.65 0 01-8.457-4.287 4.106 4.106 0 001.27 5.477A4.072 4.072 0 012.8 9.713v.052a4.105 4.105 0 003.292 4.022 4.095 4.095 0 01-1.853.07 4.108 4.108 0 003.834 2.85A8.233 8.233 0 012 18.407a11.616 11.616 0 006.29 1.84" />
                      </svg>
                    </a>
                    <a href="#" className="text-gray-400 hover:text-gray-500">
                      <span className="sr-only">LinkedIn</span>
                      <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"/>
                      </svg>
                    </a>
                  </div>
                </div>
                
                {/* 30-day money back guarantee */}
                {course.is_premium && (
                  <div className="border-t border-gray-200 pt-6 mt-6">
                    <div className="flex items-center">
                      <svg className="h-5 w-5 text-green-500 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                      </svg>
                      <span className="text-sm font-medium text-gray-900">30-Day Money-Back Guarantee</span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Related Courses */}
      <div className="bg-gray-50 py-12 border-t border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Students Also Bought</h2>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* This would typically be populated with actual related courses from an API */}
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="bg-white rounded-lg shadow overflow-hidden border border-gray-200">
                <div className="h-40 bg-gray-300"></div>
                <div className="p-4">
                  <h3 className="text-lg font-medium text-gray-900 mb-1">Related Course {i}</h3>
                  <div className="flex items-center mb-2">
                    <div className="flex items-center">
                      {[0, 1, 2, 3, 4].map((rating) => (
                        <svg 
                          key={rating} 
                          className={`h-4 w-4 ${rating < 4 ? 'text-yellow-400' : 'text-gray-300'}`}
                          xmlns="http://www.w3.org/2000/svg" 
                          viewBox="0 0 20 20" 
                          fill="currentColor"
                        >
                          <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                        </svg>
                      ))}
                    </div>
                    <p className="ml-1 text-sm text-gray-500">4.5 (500)</p>
                  </div>
                  <p className="text-primary-600 font-bold">$49.99</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default CourseDetailPage;