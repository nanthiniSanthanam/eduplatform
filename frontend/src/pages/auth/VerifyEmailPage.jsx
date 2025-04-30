/**
 * File: frontend/src/pages/auth/VerifyEmailPage.jsx
 * Purpose: Handles email verification process and resend functionality
 * Last Updated: 2025-04-29 16:41:25
 * Updated By: cadsanthanam
 * 
 * Key features:
 * 1. Verifies email tokens automatically from URL query parameters
 * 2. Shows success/error messages based on verification result
 * 3. Provides option to request a new verification email
 * 4. Directs users to next steps after verification
 * 5. Handles "already verified" state elegantly
 * 6. Auto-redirects after successful verification with countdown
 * 7. Validates email format before submission
 * 
 * API Endpoints Used:
 * - POST /api/user/email/verify/ - Verify email with token
 * - POST /api/user/email/verify/resend/ - Resend verification email
 * 
 * Implementation notes:
 * - Uses token from URL query params using useSearchParams
 * - Connects with authService (verifyEmail, resendVerification) for API communication
 * - Handles various verification states with proper UI feedback
 * - Special handling for "already verified" error as a success state
 * 
 * Variables to modify if needed:
 * - redirectPath: Where to send the user after successful verification (default: '/login')
 * - redirectDelay: How many seconds to wait before auto-redirect (default: 5)
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Link, useSearchParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

const VerifyEmailPage = () => {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');
  const { verifyEmail, resendVerification, currentUser } = useAuth();
  const navigate = useNavigate();
  
  // Configuration variables
  const redirectPath = '/login';
  const redirectDelay = 5; // seconds before auto-redirect
  
  const [verificationState, setVerificationState] = useState({
    status: token ? 'verifying' : 'manual',
    message: token ? 'Verifying your email...' : 'Please verify your email'
  });

  const [email, setEmail] = useState('');
  const [countdown, setCountdown] = useState(redirectDelay);
  const [emailError, setEmailError] = useState('');
  
  // Initialize email field if user is logged in
  useEffect(() => {
    if (currentUser && currentUser.email) {
      setEmail(currentUser.email);
    }
  }, [currentUser]);
  
  // Handle countdown for automatic redirect
  useEffect(() => {
    let timer;
    if (verificationState.status === 'success' && countdown > 0) {
      timer = setTimeout(() => {
        setCountdown(countdown - 1);
      }, 1000);
    } else if (verificationState.status === 'success' && countdown === 0) {
      navigate(redirectPath);
    }
    
    return () => {
      if (timer) clearTimeout(timer);
    };
  }, [countdown, verificationState.status, navigate, redirectPath]);

  const verifyToken = useCallback(async () => {
    if (token) {
      try {
        setVerificationState({
          status: 'verifying',
          message: 'Verifying your email...'
        });
        
        const result = await verifyEmail(token);
        if (result.success) {
          setVerificationState({
            status: 'success',
            message: 'Your email has been successfully verified!'
          });
        } else {
          setVerificationState({
            status: 'error',
            message: result.error || 'Failed to verify email. The token may be invalid or expired.'
          });
        }
      } catch (error) {
        // Check for network errors
        if (!navigator.onLine) {
          setVerificationState({
            status: 'error',
            message: 'No internet connection. Please check your connection and try again.'
          });
        } else {
          // Parse server error message if available
          const serverMessage = error.response?.data?.detail || error.message || 'An error occurred during verification.';
          setVerificationState({
            status: 'error',
            message: serverMessage
          });
        }
      }
    }
  }, [token, verifyEmail]);
  
  useEffect(() => {
    if (token) {
      verifyToken();
    }
  }, [token, verifyToken]);

  // Email validation function
  const validateEmail = (email) => {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
  };

  const handleResendVerification = async () => {
    // Clear previous errors
    setEmailError('');
    
    if (!email) {
      setEmailError('Please enter your email address');
      return;
    }
    
    if (!validateEmail(email)) {
      setEmailError('Please enter a valid email address');
      return;
    }

    try {
      setVerificationState({
        status: 'sending',
        message: 'Sending verification email...'
      });

      await resendVerification(email);

      setVerificationState({
        status: 'sent',
        message: 'A new verification email has been sent. Please check your inbox.'
      });
    } catch (error) {
      // Handle "already verified" as a success case
      if (error.response?.data?.detail === "Email address is already verified.") {
        setVerificationState({
          status: 'success',
          message: 'This email is already verified! You can proceed to login.'
        });
        return;
      }
      
      // Handle network errors
      if (!navigator.onLine) {
        setVerificationState({
          status: 'error',
          message: 'No internet connection. Please check your connection and try again.'
        });
      } else {
        // Parse server error message if available
        const serverMessage = error.response?.data?.detail || error.message || 'Failed to resend verification email';
        setVerificationState({
          status: 'error',
          message: serverMessage
        });
      }
    }
  };

  const renderEmailForm = () => (
    <div className="mt-1">
      <input
        id="email"
        name="email"
        type="email"
        autoComplete="email"
        placeholder="Enter your email address"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        className={`appearance-none block w-full px-3 py-2 border ${
          emailError ? 'border-red-500' : 'border-gray-300'
        } rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm mb-2`}
      />
      {emailError && <p className="text-red-500 text-xs mb-2">{emailError}</p>}
      <button
        onClick={handleResendVerification}
        className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
      >
        Resend Verification Email
      </button>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
          Email Verification
        </h2>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
          {verificationState.status === 'verifying' && (
            <div className="flex flex-col items-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-700"></div>
              <p className="mt-4 text-gray-600">{verificationState.message}</p>
            </div>
          )}

          {verificationState.status === 'success' && (
            <div className="text-center">
              <svg className="mx-auto h-12 w-12 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
              </svg>
              <p className="mt-4 text-lg text-gray-800">{verificationState.message}</p>
              <div className="mt-6">
                <p className="text-sm text-gray-600 mb-4">
                  Redirecting to login in {countdown} seconds...
                </p>
                <Link to={redirectPath} className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500">
                  Go to Login Now
                </Link>
              </div>
            </div>
          )}

          {verificationState.status === 'error' && (
            <div className="text-center">
              <svg className="mx-auto h-12 w-12 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
              <p className="mt-4 text-lg text-red-800">{verificationState.message}</p>
              <div className="mt-6">
                <p className="mb-4 text-sm text-gray-600">Need a new verification link?</p>
                {renderEmailForm()}
              </div>
            </div>
          )}

          {verificationState.status === 'manual' && (
            <div className="text-center">
              <svg className="mx-auto h-12 w-12 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
              <p className="mt-4 text-lg text-gray-800">Please verify your email address</p>
              <p className="mt-2 text-sm text-gray-600">
                We've sent you a verification email. Click the link in the email to verify your account.
              </p>
              <div className="mt-6">
                <p className="mb-4 text-sm text-gray-600">Didn't receive an email?</p>
                {renderEmailForm()}
              </div>
            </div>
          )}

          {verificationState.status === 'sending' && (
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-700 mx-auto"></div>
              <p className="mt-4 text-gray-600">{verificationState.message}</p>
            </div>
          )}

          {verificationState.status === 'sent' && (
            <div className="text-center">
              <svg className="mx-auto h-12 w-12 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
              <p className="mt-4 text-lg text-gray-800">{verificationState.message}</p>
              <div className="mt-6">
                <Link to={redirectPath} className="text-primary-600 hover:text-primary-500">
                  Return to login
                </Link>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default VerifyEmailPage;