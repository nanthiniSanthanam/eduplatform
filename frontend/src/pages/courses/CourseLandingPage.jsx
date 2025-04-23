import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button, Card, Rating, Badge, AnimatedElement } from '../../components/common';
import { Header } from '../../components/layouts';
import { courseService } from '../../services/api';
import { useAuth } from '../../contexts/AuthContext';

const CourseLandingPage = () => {
  const { courseSlug } = useParams();
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [course, setCourse] = useState(null);
  const [enrolled, setEnrolled] = useState(false);

  useEffect(() => {
    const fetchCourse = async () => {
      try {
        setLoading(true);
        const response = await courseService.getCourseBySlug(courseSlug);
        setCourse(response.data);
        setEnrolled(response.data.is_enrolled || false);
        setLoading(false);
      } catch (err) {
        console.error('Failed to load course data:', err);
        setError('Failed to load course information. Please try again later.');
        setLoading(false);
      }
    };

    fetchCourse();
  }, [courseSlug]);

  const handleEnroll = async () => {
    if (!isAuthenticated()) {
      navigate('/login', { state: { from: `/courses/${courseSlug}/landing` } });
      return;
    }

    try {
      await courseService.enrollInCourse(courseSlug);
      setEnrolled(true);
    } catch (err) {
      console.error('Failed to enroll:', err);
      setError('Failed to enroll in the course. Please try again.');
    }
  };

  const handleStartLearning = () => {
    if (course?.modules?.length > 0) {
      const firstModule = course.modules[0];
      const firstLesson = firstModule.lessons?.[0];
      
      if (firstLesson) {
        navigate(`/courses/${courseSlug}/content/${firstModule.id}/${firstLesson.id}`);
      } else {
        navigate(`/courses/${courseSlug}/content/${firstModule.id}/1`);
      }
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col min-h-screen">
        <Header />
        <div className="flex-grow flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-700 mx-auto mb-4"></div>
            <p className="text-primary-700 font-medium">Loading course information...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col min-h-screen">
        <Header />
        <div className="flex-grow flex items-center justify-center">
          <div className="text-center max-w-md mx-auto">
            <div className="bg-red-50 border-l-4 border-red-500 p-4 mb-4">
              <p className="text-red-700">{error}</p>
            </div>
            <Button 
              color="primary" 
              onClick={() => navigate('/courses')}
            >
              Back to Courses
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col min-h-screen bg-gray-50">
      {/* Hero Section */}
      <div className="bg-gradient-to-r from-primary-600 to-primary-800 text-white py-16 px-4">
        <div className="container mx-auto max-w-5xl">
          <div className="flex flex-col md:flex-row items-center justify-between">
            <div className="md:w-3/5 mb-8 md:mb-0">
              <h1 className="text-3xl md:text-4xl font-bold mb-4 font-display">
                {course?.title}
              </h1>
              <p className="text-lg md:text-xl mb-6 text-blue-100">
                {course?.subtitle}
              </p>
              <div className="flex items-center mb-6">
                <Rating value={course?.rating || 0} />
                <span className="ml-2 text-blue-100">
                  ({course?.rating || 0}) • {course?.enrolled_students || 0} students
                </span>
              </div>
              <div className="space-y-2 mb-6">
                <div className="flex items-center">
                  <i className="fas fa-user-graduate mr-3 text-blue-300"></i>
                  <span>Created by {course?.instructors?.map(i => i.instructor.first_name + ' ' + i.instructor.last_name).join(', ')}</span>
                </div>
                <div className="flex items-center">
                  <i className="fas fa-clock mr-3 text-blue-300"></i>
                  <span>{course?.duration}</span>
                </div>
                <div className="flex items-center">
                  <i className="fas fa-signal mr-3 text-blue-300"></i>
                  <span>{course?.level}</span>
                </div>
                {course?.has_certificate && (
                  <div className="flex items-center">
                    <i className="fas fa-certificate mr-3 text-blue-300"></i>
                    <span>Certificate of completion</span>
                  </div>
                )}
              </div>
              <div>
                {enrolled ? (
                  <Button 
                    color="secondary" 
                    size="large"
                    onClick={handleStartLearning}
                  >
                    Continue Learning
                  </Button>
                ) : (
                  <Button 
                    color="secondary" 
                    size="large"
                    onClick={handleEnroll}
                  >
                    Enroll Now
                  </Button>
                )}
              </div>
            </div>
            <div className="md:w-2/5">
              <Card className="overflow-hidden">
                <div className="aspect-w-16 aspect-h-9 bg-gray-300">
                  {course?.thumbnail ? (
                    <img 
                      src={course.thumbnail} 
                      alt={course.title} 
                      className="object-cover w-full h-full"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center bg-gray-200 text-gray-500">
                      <span>Course Preview</span>
                    </div>
                  )}
                </div>
                <div className="p-6">
                  <div className="flex justify-between items-center mb-4">
                    <div>
                      <span className="text-2xl font-bold">${course?.discount_price || course?.price}</span>
                      {course?.discount_price && (
                        <span className="text-gray-400 line-through ml-2">${course?.price}</span>
                      )}
                    </div>
                    {course?.discount_price && (
                      <Badge color="secondary">
                        {Math.round((1 - course.discount_price / course.price) * 100)}% OFF
                      </Badge>
                    )}
                  </div>
                  <div className="space-y-4">
                    <p className="flex items-center text-sm">
                      <i className="fas fa-infinity mr-3 text-gray-600"></i>
                      <span>Full lifetime access</span>
                    </p>
                    <p className="flex items-center text-sm">
                      <i className="fas fa-mobile-alt mr-3 text-gray-600"></i>
                      <span>Access on mobile and desktop</span>
                    </p>
                    {course?.has_certificate && (
                      <p className="flex items-center text-sm">
                        <i className="fas fa-certificate mr-3 text-gray-600"></i>
                        <span>Certificate of completion</span>
                      </p>
                    )}
                  </div>
                </div>
              </Card>
            </div>
          </div>
        </div>
      </div>
      
      {/* Course Content */}
      <div className="container mx-auto max-w-5xl py-12 px-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="md:col-span-2">
            {/* Description */}
            <AnimatedElement type="fade-in">
              <section className="mb-12">
                <h2 className="text-2xl font-bold mb-6 font-display">About This Course</h2>
                <div 
                  className="prose prose-blue max-w-none"
                  dangerouslySetInnerHTML={{ __html: course?.description }}
                />
              </section>
            </AnimatedElement>
            
            {/* What you'll learn */}
            {course?.skills?.length > 0 && (
              <AnimatedElement type="fade-in" delay={100}>
                <section className="mb-12">
                  <h2 className="text-2xl font-bold mb-6 font-display">What You'll Learn</h2>
                  <div className="bg-white p-6 rounded-xl shadow-sm">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {course.skills.map((skill, index) => (
                        <div key={index} className="flex items-start">
                          <i className="fas fa-check text-green-500 mt-1 mr-3"></i>
                          <span>{skill}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </section>
              </AnimatedElement>
            )}
            
            {/* Course Content */}
            <AnimatedElement type="fade-in" delay={200}>
              <section className="mb-12">
                <h2 className="text-2xl font-bold mb-6 font-display">Course Content</h2>
                <div className="bg-white rounded-xl shadow-sm overflow-hidden">
                  <div className="p-4 bg-gray-50 border-b">
                    <div className="flex justify-between items-center">
                      <span className="font-medium">{course?.modules?.length || 0} modules • {course?.duration}</span>
                    </div>
                  </div>
                  {course?.modules?.map((module, index) => (
                    <div key={module.id} className="border-b last:border-b-0">
                      <div className="p-4 hover:bg-gray-50 cursor-pointer">
                        <div className="flex justify-between items-center">
                          <h3 className="font-medium">
                            <span className="text-primary-600 mr-2">{index + 1}.</span> 
                            {module.title}
                          </h3>
                          <div className="text-sm text-gray-500">
                            {module.lessons_count || 0} lessons • {module.duration}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            </AnimatedElement>
            
            {/* Requirements */}
            {course?.requirements?.length > 0 && (
              <AnimatedElement type="fade-in" delay={300}>
                <section className="mb-12">
                  <h2 className="text-2xl font-bold mb-6 font-display">Requirements</h2>
                  <div className="bg-white p-6 rounded-xl shadow-sm">
                    <ul className="space-y-2">
                      {course.requirements.map((req, index) => (
                        <li key={index} className="flex items-start">
                          <i className="fas fa-circle text-xs text-primary-500 mt-1.5 mr-3"></i>
                          <span>{req}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </section>
              </AnimatedElement>
            )}
          </div>
          
          {/* Sidebar */}
          <div>
            {/* Instructor */}
            <AnimatedElement type="fade-in" delay={400}>
              <section className="mb-8">
                <h3 className="text-xl font-bold mb-4 font-display">Instructor</h3>
                <div className="bg-white p-6 rounded-xl shadow-sm">
                  {course?.instructors?.map(instructor => (
                    <div key={instructor.instructor.id} className="mb-4 last:mb-0">
                      <div className="flex items-center mb-3">
                        <div className="w-12 h-12 rounded-full bg-gray-200 mr-4 flex items-center justify-center text-gray-500 overflow-hidden">
                          {instructor.instructor.first_name[0]}{instructor.instructor.last_name[0]}
                        </div>
                        <div>
                          <h4 className="font-medium">
                            {instructor.instructor.first_name} {instructor.instructor.last_name}
                          </h4>
                          <p className="text-sm text-gray-500">{instructor.title}</p>
                        </div>
                      </div>
                      {instructor.bio && (
                        <p className="text-gray-600 text-sm">{instructor.bio}</p>
                      )}
                    </div>
                  ))}
                </div>
              </section>
            </AnimatedElement>
            
            {/* Take Action Card */}
            <AnimatedElement type="fade-in" delay={500}>
              <section>
                <div className="sticky top-6 bg-white p-6 rounded-xl shadow-sm border-t-4 border-primary-500">
                  <h3 className="text-xl font-bold mb-4 font-display">Ready to Start Learning?</h3>
                  <p className="text-gray-600 mb-6">
                    Join {course?.enrolled_students || 0} students who are already taking this course.
                  </p>
                  {enrolled ? (
                    <Button 
                      color="primary" 
                      size="large"
                      className="w-full"
                      onClick={handleStartLearning}
                    >
                      Continue Learning
                    </Button>
                  ) : (
                    <Button 
                      color="primary" 
                      size="large"
                      className="w-full"
                      onClick={handleEnroll}
                    >
                      Enroll Now
                    </Button>
                  )}
                </div>
              </section>
            </AnimatedElement>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CourseLandingPage;