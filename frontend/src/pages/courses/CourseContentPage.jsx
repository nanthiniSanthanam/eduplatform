import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  Button, 
  Card, 
  Badge, 
  ProgressBar, 
  Tabs, 
  Accordion, 
  AnimatedElement,
  Tooltip,
  Alert
} from '../../components/common';
import { Header } from '../../components/layouts';
import { courseService, noteService } from '../../services/api';
import { useAuth } from '../../contexts/AuthContext';

const CourseContentPage = () => {
  const { courseSlug, moduleId = '1', lessonId = '1' } = useParams();
  const navigate = useNavigate();
  const { currentUser, isAuthenticated } = useAuth();
  const [activeTab, setActiveTab] = useState('content');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [courseData, setCourseData] = useState(null);
  const [currentModule, setCurrentModule] = useState(null);
  const [currentLesson, setCurrentLesson] = useState(null);
  const [userNotes, setUserNotes] = useState([]);
  const [noteContent, setNoteContent] = useState('');
  const [progress, setProgress] = useState({
    completed: 0,
    total: 0,
    percentage: 0
  });

  // Check authentication
  useEffect(() => {
    if (!loading && !isAuthenticated()) {
      navigate('/login', { state: { from: `/courses/${courseSlug}/content/${moduleId}/${lessonId}` } });
    }
  }, [loading, isAuthenticated, navigate, courseSlug, moduleId, lessonId]);

  // Load course data
  useEffect(() => {
    const fetchCourseData = async () => {
      try {
        setLoading(true);
        
        // Get module details including lessons
        const moduleResponse = await courseService.getModuleDetails(moduleId);
        setCurrentModule(moduleResponse.data);
        
        // Get course data from the module's parent course
        const courseResponse = await courseService.getCourseBySlug(courseSlug);
        setCourseData(courseResponse.data);
        
        // Get the current lesson
        const lessonResponse = await courseService.getLessonDetails(lessonId);
        setCurrentLesson(lessonResponse.data);
        
        // Get user progress
        if (courseResponse.data.user_progress) {
          setProgress(courseResponse.data.user_progress);
        }
        
        setLoading(false);
      } catch (err) {
        console.error('Failed to load course data:', err);
        setError('Failed to load course content. Please try again later.');
        setLoading(false);
      }
    };

    if (isAuthenticated()) {
      fetchCourseData();
    }
  }, [courseSlug, moduleId, lessonId, isAuthenticated]);

  // Load user notes when tab changes
  useEffect(() => {
    const fetchNotes = async () => {
      if (activeTab === 'notes' && currentLesson) {
        try {
          const response = await noteService.getNotesForLesson(currentLesson.id);
          setUserNotes(response.data);
        } catch (err) {
          console.error('Failed to load notes:', err);
        }
      }
    };

    if (isAuthenticated()) {
      fetchNotes();
    }
  }, [activeTab, currentLesson, isAuthenticated]);

  // Handle saving a note
  const handleSaveNote = async () => {
    if (!noteContent.trim() || !currentLesson) return;
    
    try {
      await noteService.createNote({
        lesson: currentLesson.id,
        content: noteContent
      });
      
      // Refresh notes
      const response = await noteService.getNotesForLesson(currentLesson.id);
      setUserNotes(response.data);
      setNoteContent('');
    } catch (err) {
      console.error('Failed to save note:', err);
    }
  };

  // Handle completing a lesson
  const completeLesson = async () => {
    if (!currentLesson) return;
    
    try {
      const response = await courseService.completeLesson(currentLesson.id);
      
      // Update progress
      setProgress(response.data.progress);
      
      // Update lesson in state
      setCurrentLesson(prev => ({
        ...prev,
        is_completed: true
      }));
    } catch (err) {
      console.error('Failed to mark lesson as complete:', err);
    }
  };

  // Navigation between lessons
  const navigateToLesson = (moduleId, lessonId) => {
    navigate(`/courses/${courseSlug}/content/${moduleId}/${lessonId}`);
  };

  // Find next and previous lessons
  const findNavigation = () => {
    if (!courseData || !currentModule) return { prevLink: null, nextLink: null };
    
    // Get all modules
    const modules = courseData.modules;
    
    // Find current module index
    const currentModuleIndex = modules.findIndex(m => m.id.toString() === moduleId);
    
    // Find current lesson index
    const lessons = currentModule.lessons;
    const currentLessonIndex = lessons.findIndex(l => l.id.toString() === lessonId);
    
    let prevLink = null;
    let nextLink = null;
    
    // Previous lesson
    if (currentLessonIndex > 0) {
      // Previous lesson in same module
      prevLink = {
        moduleId,
        lessonId: lessons[currentLessonIndex - 1].id
      };
    } else if (currentModuleIndex > 0) {
      // Last lesson of previous module
      const prevModule = modules[currentModuleIndex - 1];
      // We'd need to load the previous module's lessons
      // For simplicity, we'll just navigate to the module
      prevLink = {
        moduleId: prevModule.id,
        lessonId: '1' // Assuming at least one lesson
      };
    }
    
    // Next lesson
    if (currentLessonIndex < lessons.length - 1) {
      // Next lesson in same module
      nextLink = {
        moduleId,
        lessonId: lessons[currentLessonIndex + 1].id
      };
    } else if (currentModuleIndex < modules.length - 1) {
      // First lesson of next module
      const nextModule = modules[currentModuleIndex + 1];
      nextLink = {
        moduleId: nextModule.id,
        lessonId: '1' // Assuming at least one lesson
      };
    }
    
    return { prevLink, nextLink };
  };
  
  const { prevLink, nextLink } = findNavigation();

  // If loading or no data, show loading state
  if (loading) {
    return (
      <div className="flex flex-col min-h-screen">
        <Header />
        <div className="flex-grow flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-700 mx-auto mb-4"></div>
            <p className="text-primary-700 font-medium">Loading course content...</p>
          </div>
        </div>
      </div>
    );
  }

  // If error, show error message
  if (error) {
    return (
      <div className="flex flex-col min-h-screen">
        <Header />
        <div className="flex-grow flex items-center justify-center">
          <div className="text-center max-w-md mx-auto">
            <Alert type="error" title="Error Loading Course">
              {error}
            </Alert>
            <Button 
              color="primary" 
              className="mt-4"
              onClick={() => navigate('/courses')}
            >
              Back to Courses
            </Button>
          </div>
        </div>
      </div>
    );
  }

  // Rest of component remains the same as in the original
  return (
    <div className="flex flex-col min-h-screen bg-gray-50">
      {/* Course Header with Progress */}
      <div className="bg-white shadow-md py-3 px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between mb-2">
          <div className="flex items-center mb-2 md:mb-0">
            <button 
              onClick={() => setSidebarOpen(!sidebarOpen)} 
              className="mr-3 p-2 rounded-md hover:bg-gray-100"
              aria-label="Toggle sidebar"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
            <div>
              <h1 className="text-xl font-display font-semibold text-gray-800">
                {courseData?.title}
              </h1>
              <p className="text-sm text-gray-500">
                {courseData?.instructors?.map(i => i.instructor.first_name + ' ' + i.instructor.last_name).join(', ')}
              </p>
            </div>
          </div>

          <div className="w-full md:w-64">
            <div className="flex justify-between mb-1 text-sm">
              <span className="font-medium">Your progress</span>
              <span>{progress.percentage}% complete</span>
            </div>
            <ProgressBar 
              value={progress.percentage} 
              color="primary"
              height="small" 
            />
          </div>
        </div>
        
        {/* Current lesson info */}
        {currentModule && currentLesson && (
          <div className="flex items-center text-sm text-gray-600 pl-10">
            <span className="font-medium text-primary-700">{currentModule.title}</span>
            <span className="mx-2">›</span>
            <span>{currentLesson.title}</span>
          </div>
        )}
      </div>
      
      <div className="flex-grow flex">
        {/* Course Navigation Sidebar */}
        <div className={`bg-white shadow-md border-r border-gray-200 transition-all duration-300 ${
          sidebarOpen ? 'w-72' : 'w-0'
        } overflow-hidden lg:sticky lg:top-0 lg:h-screen`}>
          <div className="p-4">
            <h2 className="font-display font-semibold text-lg mb-4">Course Content</h2>
            
            <div className="space-y-2">
              {courseData && courseData.modules.map((module, index) => (
                <Accordion 
                  key={module.id}
                  title={
                    <div className="flex items-center justify-between w-full">
                      <div>
                        <span className="font-display text-primary-700 mr-1">Module {index + 1}:</span> 
                        <span className="font-medium">{module.title}</span>
                      </div>
                    </div>
                  }
                  defaultOpen={module.id.toString() === moduleId}
                  headerClassName={module.isCompleted ? "border-l-4 border-green-500" : ""}
                >
                  {module.id.toString() === currentModule?.id.toString() ? (
                    <div className="space-y-2 py-1">
                      {currentModule.lessons.map((lesson) => {
                        const isCompleted = progress.completed_lessons?.includes(parseInt(lesson.id)) || false;
                        const isActive = lesson.id.toString() === lessonId;
                        
                        return (
                          <div 
                            key={lesson.id}
                            className={`flex items-center pl-2 py-2 pr-3 rounded-md cursor-pointer transition-colors ${
                              isActive 
                                ? 'bg-primary-50 text-primary-900' 
                                : isCompleted 
                                  ? 'text-gray-700 hover:bg-gray-50' 
                                  : 'text-gray-600 hover:bg-gray-50'
                            }`}
                            onClick={() => navigateToLesson(module.id, lesson.id)}
                          >
                            <div className={`w-4 h-4 rounded-full flex items-center justify-center mr-2 flex-shrink-0 ${
                              isCompleted 
                                ? 'bg-green-500' 
                                : isActive 
                                  ? 'bg-primary-500' 
                                  : 'bg-gray-200'
                            }`}>
                              {isCompleted && (
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-2.5 w-2.5 text-white" viewBox="0 0 20 20" fill="currentColor">
                                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                                </svg>
                              )}
                            </div>
                            <div className="flex-grow min-w-0">
                              <div className="text-sm font-medium truncate">{lesson.title}</div>
                              <div className="flex items-center text-xs text-gray-500">
                                <span>{lesson.type}</span>
                                <span className="mx-1">•</span>
                                <span>{lesson.duration}</span>
                              </div>
                            </div>
                            {lesson.has_assessment && (
                              <Tooltip content="Includes assessment">
                                <span className="w-4 h-4 flex-shrink-0 ml-2">
                                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 text-amber-500" viewBox="0 0 20 20" fill="currentColor">
                                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
                                  </svg>
                                </span>
                              </Tooltip>
                            )}
                            {lesson.has_lab && (
                              <Tooltip content="Includes lab exercise">
                                <span className="w-4 h-4 flex-shrink-0 ml-2">
                                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 text-blue-500" viewBox="0 0 20 20" fill="currentColor">
                                    <path fillRule="evenodd" d="M7 2a1 1 0 00-.707 1.707L7 4.414v3.758a1 1 0 01-.293.707l-4 4C.817 14.769 2.156 18 4.828 18h10.343c2.673 0 4.012-3.231 2.122-5.121l-4-4A1 1 0 0113 8.172V4.414l.707-.707A1 1 0 0013 2H7zm2 6.172V4h2v4.172a3 3 0 00.879 2.12l1.027 1.028a4 4 0 00-2.171.102l-.47.156a4 4 0 01-2.53 0l-.563-.187a1.993 1.993 0 00-.114-.035l1.063-1.063A3 3 0 009 8.172z" clipRule="evenodd" />
                                  </svg>
                                </span>
                              </Tooltip>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  ) : (
                    <div className="py-2 px-2 text-sm text-gray-500 italic">
                      Select this module to view lessons
                    </div>
                  )}
                </Accordion>
              ))}
            </div>
          </div>
        </div>
        
        {/* Main Content Area */}
        <div className="flex-grow">
          <div className="container mx-auto py-6 px-4">
            {currentModule && currentLesson ? (
              <div>
                {/* Content Nav Tabs */}
                <Tabs
                  tabs={[
                    { id: 'content', label: 'Lesson Content' },
                    { id: 'resources', label: 'Resources' },
                    { id: 'notes', label: 'My Notes' },
                  ]}
                  activeTab={activeTab}
                  onChange={setActiveTab}
                  className="mb-6"
                />
                
                {/* Tab Content */}
                <div className="bg-white shadow-md rounded-xl p-6 mb-6">
                  {activeTab === 'content' && (
                    <AnimatedElement type="fade-in">
                      <div 
                        className="prose prose-primary max-w-none"
                        dangerouslySetInnerHTML={{ __html: currentLesson.content || 'Content is being prepared...' }}
                      />
                      
                      {!currentLesson.is_completed && (
                        <div className="mt-8 border-t pt-6">
                          <Button 
                            color="primary" 
                            size="medium" 
                            onClick={completeLesson}
                          >
                            Mark as Completed
                          </Button>
                        </div>
                      )}
                      
                      {currentLesson.has_assessment && (
                        <div className="mt-8 border-t pt-6">
                          <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 flex items-start">
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-amber-500 mr-3 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            <div>
                              <h3 className="font-semibold text-amber-800 mb-1">Knowledge Check</h3>
                              <p className="text-amber-700 mb-3">Complete this quick assessment to check your understanding of the key concepts in this lesson.</p>
                              <Button 
                                color="secondary" 
                                size="small" 
                                className="font-medium"
                                onClick={() => navigate(`/courses/${courseSlug}/assessment/${currentLesson.id}`)}
                              >
                                Start Assessment
                              </Button>
                            </div>
                          </div>
                        </div>
                      )}
                      
                      {currentLesson.has_lab && (
                        <div className="mt-8 border-t pt-6">
                          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 flex items-start">
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-blue-500 mr-3 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
                            </svg>
                            <div>
                              <h3 className="font-semibold text-blue-800 mb-1">Hands-on Lab Exercise</h3>
                              <p className="text-blue-700 mb-3">Apply what you've learned in this interactive lab environment.</p>
                              <Button 
                                color="primary" 
                                size="small" 
                                className="font-medium"
                                onClick={() => navigate(`/courses/${courseSlug}/lab/${currentLesson.id}`)}
                              >
                                Open Virtual Lab
                              </Button>
                            </div>
                          </div>
                        </div>
                      )}
                    </AnimatedElement>
                  )}
                  
                  {activeTab === 'resources' && (
                    <AnimatedElement type="fade-in">
                      <h3 className="text-xl font-display font-semibold mb-4">Additional Resources</h3>
                      {currentLesson.resources && currentLesson.resources.length > 0 ? (
                        <div className="grid gap-4 md:grid-cols-2">
                          {currentLesson.resources.map((resource) => (
                            <Card key={resource.id} className="p-4 hover:shadow-md transition-shadow">
                              <div className="flex items-start">
                                <div className="mr-3 text-primary-600">
                                  {resource.type === 'document' && (
                                    <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                                    </svg>
                                  )}
                                  {resource.type === 'video' && (
                                    <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                                    </svg>
                                  )}
                                  {resource.type === 'link' && (
                                    <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                                    </svg>
                                  )}
                                  {resource.type === 'code' && (
                                    <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
                                    </svg>
                                  )}
                                  {resource.type === 'tool' && (
                                    <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                    </svg>
                                  )}
                                </div>
                                <div>
                                  <h4 className="font-medium text-primary-800 mb-1">{resource.title}</h4>
                                  <p className="text-sm text-gray-600 mb-2">{resource.description}</p>
                                  {resource.file && (
                                    <a 
                                      href={resource.file} 
                                      className="text-sm text-primary-600 hover:text-primary-800 font-medium flex items-center"
                                      target="_blank"
                                      rel="noopener noreferrer"
                                    >
                                      Download
                                      <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 ml-1" viewBox="0 0 20 20" fill="currentColor">
                                        <path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clipRule="evenodd" />
                                      </svg>
                                    </a>
                                  )}
                                  {resource.url && (
                                    <a 
                                      href={resource.url} 
                                      className="text-sm text-primary-600 hover:text-primary-800 font-medium flex items-center"
                                      target="_blank"
                                      rel="noopener noreferrer"
                                    >
                                      Visit Resource
                                      <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 ml-1" viewBox="0 0 20 20" fill="currentColor">
                                        <path d="M11 3a1 1 0 100 2h2.586l-6.293 6.293a1 1 0 101.414 1.414L15 6.414V9a1 1 0 102 0V4a1 1 0 00-1-1h-5z" />
                                        <path d="M5 5a2 2 0 00-2 2v8a2 2 0 002 2h8a2 2 0 002-2v-3a1 1 0 10-2 0v3H5V7h3a1 1 0 000-2H5z" />
                                      </svg>
                                    </a>
                                  )}
                                </div>
                              </div>
                            </Card>
                          ))}
                        </div>
                      ) : (
                        <div className="text-center py-8 bg-gray-50 rounded-lg">
                          <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 text-gray-400 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                          </svg>
                          <p className="text-gray-600">No additional resources are available for this lesson.</p>
                        </div>
                      )}
                    </AnimatedElement>
                  )}
                  
                  {activeTab === 'notes' && (
                    <AnimatedElement type="fade-in">
                      <div>
                        <div className="flex justify-between items-center mb-4">
                          <h3 className="text-xl font-display font-semibold">My Notes</h3>
                        </div>
                        
                        <div className="mb-6">
                          <textarea 
                            className="w-full h-48 p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors"
                            placeholder="Type your notes here..."
                            value={noteContent}
                            onChange={(e) => setNoteContent(e.target.value)}
                          ></textarea>
                          <div className="flex justify-end mt-2">
                            <Button 
                              color="primary" 
                              size="small"
                              onClick={handleSaveNote}
                              disabled={!noteContent.trim()}
                            >
                              Save Note
                            </Button>
                          </div>
                        </div>
                        
                        {userNotes.length > 0 ? (
                          <div className="space-y-4">
                            {userNotes.map(note => (
                              <div key={note.id} className="bg-gray-50 p-4 rounded-lg">
                                <div className="flex justify-between items-start mb-2">
                                  <div className="text-sm text-gray-500">
                                    {new Date(note.created_date).toLocaleDateString('en-US', {
                                      year: 'numeric',
                                      month: 'long',
                                      day: 'numeric',
                                      hour: '2-digit',
                                      minute: '2-digit'
                                    })}
                                  </div>
                                  <div className="flex space-x-2">
                                    <button 
                                      className="text-primary-600 hover:text-primary-800 text-sm"
                                      onClick={() => {
                                        setNoteContent(note.content);
                                      }}
                                    >
                                      Edit
                                    </button>
                                    <button 
                                      className="text-red-600 hover:text-red-800 text-sm"
                                      onClick={async () => {
                                        try {
                                          await noteService.deleteNote(note.id);
                                          setUserNotes(userNotes.filter(n => n.id !== note.id));
                                        } catch (err) {
                                          console.error('Failed to delete note:', err);
                                        }
                                      }}
                                    >
                                      Delete
                                    </button>
                                  </div>
                                </div>
                                <p className="text-gray-700 whitespace-pre-wrap">{note.content}</p>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <div className="text-center py-8 bg-gray-50 rounded-lg">
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 text-gray-400 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                            </svg>
                            <p className="text-gray-600">You haven't added any notes for this lesson yet.</p>
                          </div>
                        )}
                      </div>
                    </AnimatedElement>
                  )}
                </div>
                
                {/* Navigation Buttons */}
                <div className="flex justify-between mt-6">
                  <Button
                    color="light"
                    disabled={!prevLink}
                    onClick={() => prevLink && navigateToLesson(prevLink.moduleId, prevLink.lessonId)}
                    iconLeft={
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    }
                  >
                    Previous Lesson
                  </Button>
                  <Button
                    color="primary"
                    disabled={!nextLink}
                    onClick={() => nextLink && navigateToLesson(nextLink.moduleId, nextLink.lessonId)}
                    iconRight={
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                      </svg>
                    }
                  >
                    {nextLink ? 'Next Lesson' : 'Complete Module'}
                  </Button>
                </div>
              </div>
            ) : (
              <div className="text-center py-10">
                <div className="mb-4">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-16 w-16 text-gray-400 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <h2 className="text-xl font-semibold text-gray-700 mb-2">Lesson Not Found</h2>
                <p className="text-gray-500 mb-4">The lesson you are looking for doesn't exist or has been moved.</p>
                <Button 
                  color="primary" 
                  onClick={() => navigate(`/courses/${courseSlug}`)}
                >
                  Back to Course
                </Button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default CourseContentPage;