import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button, Card, ProgressBar, Alert, Badge } from '../../components/common';
import { Header } from '../../components/layouts';
import { assessmentService, courseService } from '../../services/api';
import { useAuth } from '../../contexts/AuthContext';

const AssessmentPage = () => {
  const { courseSlug, lessonId } = useParams();
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [assessment, setAssessment] = useState(null);
  const [attempt, setAttempt] = useState(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState({});
  const [timeRemaining, setTimeRemaining] = useState(null);
  const [hasSubmitted, setHasSubmitted] = useState(false);
  const [results, setResults] = useState(null);
  
  // Check authentication
  useEffect(() => {
    if (!isAuthenticated()) {
      navigate('/login', { state: { from: `/courses/${courseSlug}/assessment/${lessonId}` } });
    }
  }, [isAuthenticated, navigate, courseSlug, lessonId]);

  // Load assessment data
  useEffect(() => {
    const fetchAssessment = async () => {
      try {
        setLoading(true);
        
        // First, get the lesson details to find the assessment ID
        const lessonResponse = await courseService.getLessonDetails(lessonId);
        
        if (!lessonResponse.data.has_assessment) {
          throw new Error('This lesson does not have an assessment.');
        }
        
        // Get the assessment details
        const assessmentResponse = await assessmentService.getAssessmentDetails(lessonResponse.data.assessment_id);
        setAssessment(assessmentResponse.data);
        
        if (assessmentResponse.data.time_limit > 0) {
          setTimeRemaining(assessmentResponse.data.time_limit * 60); // Convert minutes to seconds
        }
        
        setLoading(false);
      } catch (err) {
        console.error('Failed to load assessment:', err);
        setError(err.message || 'Failed to load assessment. Please try again later.');
        setLoading(false);
    } 
  };

  if (isAuthenticated()) {
    fetchAssessment();
  }
}, [lessonId, isAuthenticated, courseSlug]);

// Timer countdown
useEffect(() => {
  let timer;
  
  if (timeRemaining !== null && timeRemaining > 0 && attempt && !hasSubmitted) {
    timer = setInterval(() => {
      setTimeRemaining(prev => {
        if (prev <= 1) {
          clearInterval(timer);
          handleSubmit();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  }
  
  return () => {
    if (timer) clearInterval(timer);
  };
}, [timeRemaining, attempt, hasSubmitted]);

// Format time remaining
const formatTimeRemaining = () => {
  if (timeRemaining === null) return '';
  
  const minutes = Math.floor(timeRemaining / 60);
  const seconds = timeRemaining % 60;
  
  return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
};

// Start the assessment
const handleStart = async () => {
  try {
    const response = await assessmentService.startAssessment(assessment.id);
    setAttempt(response.data);
  } catch (err) {
    console.error('Failed to start assessment:', err);
    setError('Failed to start the assessment. Please try again.');
  }
};

// Handle answer selection
const handleAnswerSelect = (questionId, answerId) => {
  setAnswers(prev => ({
    ...prev,
    [questionId]: answerId
  }));
};

// Handle text answer input
const handleTextAnswer = (questionId, value) => {
  setAnswers(prev => ({
    ...prev,
    [questionId]: value
  }));
};

// Go to next question
const handleNextQuestion = () => {
  if (currentQuestionIndex < assessment.questions.length - 1) {
    setCurrentQuestionIndex(prev => prev + 1);
  }
};

// Go to previous question
const handlePrevQuestion = () => {
  if (currentQuestionIndex > 0) {
    setCurrentQuestionIndex(prev => prev - 1);
  }
};

// Submit the assessment
const handleSubmit = async () => {
  try {
    setHasSubmitted(true);
    
    // Format answers for API
    const answersForSubmission = Object.entries(answers).map(([questionId, value]) => ({
      question_id: parseInt(questionId),
      answer_id: typeof value === 'string' ? null : parseInt(value),
      text_answer: typeof value === 'string' ? value : ''
    }));
    
    const response = await assessmentService.submitAssessment(attempt.id, answersForSubmission);
    setResults(response.data);
  } catch (err) {
    console.error('Failed to submit assessment:', err);
    setError('Failed to submit your assessment. Please try again.');
  }
};

// Navigate back to the lesson
const handleReturnToLesson = () => {
  // Extract module ID from the lesson 
  const moduleId = '1'; // In a real app, get this from the lesson data or URL
  navigate(`/courses/${courseSlug}/content/${moduleId}/${lessonId}`);
};

// If loading, show loading state
if (loading) {
  return (
    <div className="flex flex-col min-h-screen">
      <Header />
      <div className="flex-grow flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-700 mx-auto mb-4"></div>
          <p className="text-primary-700 font-medium">Loading assessment...</p>
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
          <Alert type="error" title="Error Loading Assessment">
            {error}
          </Alert>
          <Button 
            color="primary" 
            className="mt-4"
            onClick={handleReturnToLesson}
          >
            Back to Lesson
          </Button>
        </div>
      </div>
    </div>
  );
}

// Render assessment start screen
if (assessment && !attempt && !results) {
  return (
    <div className="flex flex-col min-h-screen bg-gray-50">
      <Header />
      <div className="container mx-auto py-12 px-4">
        <Card className="max-w-xl mx-auto p-8">
          <div className="text-center mb-6">
            <h1 className="text-2xl font-display font-bold text-gray-900 mb-2">
              {assessment.title}
            </h1>
            <p className="text-gray-600">{assessment.description}</p>
          </div>
          
          <div className="mb-8">
            <div className="bg-blue-50 border-l-4 border-blue-500 p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-blue-500" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-blue-800">Assessment Information</h3>
                  <div className="mt-2 text-sm text-blue-700 space-y-1">
                    <p>• {assessment.questions.length} questions</p>
                    {assessment.time_limit > 0 && (
                      <p>• Time limit: {assessment.time_limit} minutes</p>
                    )}
                    <p>• Passing score: {assessment.passing_score}%</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <div className="text-center">
            <Button 
              color="primary" 
              size="large"
              className="w-full sm:w-auto"
              onClick={handleStart}
            >
              Start Assessment
            </Button>
            <p className="mt-4 text-sm text-gray-500">
              You can return to the lesson at any time by clicking "Exit"
            </p>
          </div>
        </Card>
      </div>
    </div>
  );
}

// Render results screen
if (results) {
  const isPassed = results.passed;
  const scorePercentage = results.score_percentage;
  
  return (
    <div className="flex flex-col min-h-screen bg-gray-50">
      <Header />
      <div className="container mx-auto py-12 px-4">
        <Card className="max-w-xl mx-auto p-8">
          <div className={`text-center mb-8 ${isPassed ? 'text-green-600' : 'text-amber-600'}`}>
            {isPassed ? (
              <svg xmlns="http://www.w3.org/2000/svg" className="h-16 w-16 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            ) : (
              <svg xmlns="http://www.w3.org/2000/svg" className="h-16 w-16 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            )}
            <h1 className="text-2xl font-display font-bold mb-2">
              {isPassed ? 'Assessment Passed!' : 'Assessment Not Passed'}
            </h1>
            <p>
              You scored {Math.round(scorePercentage)}% 
              ({results.score} out of {assessment.questions.length} points)
            </p>
          </div>
          
          <div className="mb-8">
            <h3 className="text-lg font-medium mb-4">Your Results</h3>
            
            {/* Progress bar showing score */}
            <div className="mb-6">
              <ProgressBar 
                value={scorePercentage} 
                color={isPassed ? "success" : "warning"}
                height="medium"
              />
              <div className="flex justify-between text-sm mt-1">
                <span>{scorePercentage}% Your Score</span>
                <span>{assessment.passing_score}% Passing Score</span>
              </div>
            </div>
            
            {/* Show a summary of answers */}
            <div className="space-y-4">
              {results.answers.map((answer, index) => (
                <div key={index} className="flex items-center">
                  <div className={`w-6 h-6 rounded-full flex items-center justify-center mr-3 ${
                    answer.is_correct ? 'bg-green-500' : 'bg-red-500'
                  }`}>
                    <span className="text-white text-xs font-bold">{index + 1}</span>
                  </div>
                  <div className="text-sm">
                    <span className="font-medium">Question {index + 1}</span>
                    <span className="mx-2">•</span>
                    <span className={answer.is_correct ? 'text-green-600' : 'text-red-600'}>
                      {answer.is_correct ? 'Correct' : 'Incorrect'}
                    </span>
                    {answer.points_earned > 0 && (
                      <span className="ml-2 text-gray-500">
                        ({answer.points_earned} points)
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
          
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            {!isPassed && (
              <Button 
                color="secondary"
                className="order-2 sm:order-1"
                onClick={() => {
                  // Reset state to restart the assessment
                  setAttempt(null);
                  setAnswers({});
                  setCurrentQuestionIndex(0);
                  setHasSubmitted(false);
                  setResults(null);
                  
                  if (assessment.time_limit > 0) {
                    setTimeRemaining(assessment.time_limit * 60);
                  }
                }}
              >
                Retry Assessment
              </Button>
            )}
            <Button 
              color="primary"
              className="order-1 sm:order-2"
              onClick={handleReturnToLesson}
            >
              Return to Lesson
            </Button>
          </div>
        </Card>
      </div>
    </div>
  );
}

// Render assessment taking screen
const currentQuestion = assessment?.questions[currentQuestionIndex];

return (
  <div className="flex flex-col min-h-screen bg-gray-50">
    <Header />
    <div className="container mx-auto py-6 px-4">
      <div className="max-w-3xl mx-auto">
        {/* Assessment Header */}
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-xl font-display font-semibold text-gray-900">
            {assessment.title}
          </h1>
          <div className="flex items-center">
            {timeRemaining !== null && (
              <div className={`mr-4 font-mono ${timeRemaining < 60 ? 'text-red-600 animate-pulse' : 'text-gray-700'}`}>
                <span className="font-medium">{formatTimeRemaining()}</span>
              </div>
            )}
            <Button 
              color="light"
              size="small"
              onClick={handleReturnToLesson}
            >
              Exit
            </Button>
          </div>
        </div>
        
        {/* Progress indicator */}
        <div className="mb-6">
          <div className="flex justify-between text-sm mb-1">
            <span>Question {currentQuestionIndex + 1} of {assessment.questions.length}</span>
            <span>{Object.keys(answers).length} answered</span>
          </div>
          <ProgressBar 
            value={(currentQuestionIndex + 1) / assessment.questions.length * 100} 
            color="primary"
            height="small" 
          />
        </div>
        
        {/* Question Card */}
        <Card className="mb-6 p-6">
          <div className="mb-6">
            <div className="flex items-center justify-between mb-2">
              <Badge color="primary">Question {currentQuestionIndex + 1}</Badge>
              <span className="text-sm text-gray-500">
                {currentQuestion?.points} {currentQuestion?.points === 1 ? 'point' : 'points'}
              </span>
            </div>
            <h2 className="text-lg font-medium text-gray-900 mb-4">
              {currentQuestion?.question_text}
            </h2>
            
            {/* Question type-specific rendering */}
            {currentQuestion?.question_type === 'multiple_choice' && (
              <div className="space-y-3">
                {currentQuestion.answers.map(answer => (
                  <div 
                    key={answer.id}
                    className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                      answers[currentQuestion.id] === answer.id 
                        ? 'border-primary-500 bg-primary-50' 
                        : 'border-gray-200 hover:bg-gray-50'
                    }`}
                    onClick={() => handleAnswerSelect(currentQuestion.id, answer.id)}
                  >
                    <div className="flex items-center">
                      <div className={`w-5 h-5 rounded-full border flex-shrink-0 mr-3 ${
                        answers[currentQuestion.id] === answer.id 
                          ? 'border-primary-500 bg-primary-500' 
                          : 'border-gray-300'
                      }`}>
                        {answers[currentQuestion.id] === answer.id && (
                          <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                          </svg>
                        )}
                      </div>
                      <span className="text-gray-900">{answer.answer_text}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
            
            {currentQuestion?.question_type === 'true_false' && (
              <div className="space-y-3">
                {currentQuestion.answers.map(answer => (
                  <div 
                    key={answer.id}
                    className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                      answers[currentQuestion.id] === answer.id 
                        ? 'border-primary-500 bg-primary-50' 
                        : 'border-gray-200 hover:bg-gray-50'
                    }`}
                    onClick={() => handleAnswerSelect(currentQuestion.id, answer.id)}
                  >
                    <div className="flex items-center">
                      <div className={`w-5 h-5 rounded-full border flex-shrink-0 mr-3 ${
                        answers[currentQuestion.id] === answer.id 
                          ? 'border-primary-500 bg-primary-500' 
                          : 'border-gray-300'
                      }`}>
                        {answers[currentQuestion.id] === answer.id && (
                          <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                          </svg>
                        )}
                      </div>
                      <span className="text-gray-900">{answer.answer_text}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
            
            {currentQuestion?.question_type === 'short_answer' && (
              <div>
                <textarea
                  className="w-full h-32 p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  placeholder="Type your answer here..."
                  value={answers[currentQuestion.id] || ''}
                  onChange={(e) => handleTextAnswer(currentQuestion.id, e.target.value)}
                ></textarea>
              </div>
            )}
          </div>
          
          {/* Navigation buttons */}
          <div className="flex justify-between">
            <Button
              color="light"
              disabled={currentQuestionIndex === 0}
              onClick={handlePrevQuestion}
              iconLeft={
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
              }
            >
              Previous
            </Button>
            
            {currentQuestionIndex < assessment.questions.length - 1 ? (
              <Button
                color="primary"
                onClick={handleNextQuestion}
                iconRight={
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                  </svg>
                }
              >
                Next
              </Button>
            ) : (
              <Button
                color="secondary"
                onClick={handleSubmit}
              >
                Submit Assessment
              </Button>
            )}
          </div>
        </Card>
        
        {/* Question Navigation */}
        <div className="bg-white rounded-xl shadow-md p-4">
          <h3 className="text-sm font-medium text-gray-700 mb-3">Question Navigator</h3>
          <div className="flex flex-wrap gap-2">
            {assessment.questions.map((question, index) => (
              <button
                key={index}
                className={`w-8 h-8 flex items-center justify-center rounded-full text-sm font-medium transition-colors ${
                  currentQuestionIndex === index
                    ? 'bg-primary-500 text-white'
                    : answers[question.id]
                      ? 'bg-green-100 text-green-800 border border-green-300'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
                onClick={() => setCurrentQuestionIndex(index)}
              >
                {index + 1}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  </div>
);
};

export default AssessmentPage;