/**
 * File: frontend/src/pages/auth/VerifyEmailPage.jsx
 * Purpose: Handles email verification process
 * 
 * Key features:
 * 1. Verifies email tokens automatically from URL
 * 2. Shows success/error messages
 * 3. Provides option to request a new verification email
 * 4. Directs users to next steps after verification
 * 
 * Implementation notes:
 * - Uses token from URL params if available
 * - Connects with authService.verifyEmail API
 * - Handles various verification states
 */

import React, { useState, useEffect } from 'react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

const VerifyEmailPage = () => {
  const { token } = useParams();
  const { verifyEmail, currentUser } = useAuth();
  const navigate = useNavigate();
  
  const [verificationState, setVerificationState] = useState({
    status: token ? 'verifying' : 'manual',
    message: token ? 'Verifying your email...' : 'Please verify your email'
  });

  const [email, setEmail] = useState('');
  
  useEffect(() => {
    // If token is provided in URL, verify automatically
    const verifyToken = async () => {
      if (token) {
        try {
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
          setVerificationState({
            status: 'error',
            message: 'An error occurred during verification. Please try again.'
          });
        }
      }
    };

    verifyToken();
  }, [token, verifyEmail]);

  const handleResendVerification = async () => {
    if (!email) {
      setVerificationState({
        ...verificationState,
        error: 'Please enter your email address'
      });
      return;
    }

    try {
      setVerificationState({
        status: 'sending',
        message: 'Sending verification email...'
      });

      // Call API to resend verification email
      const response = await fetch('/api/users/resend-verification/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
      });

      const result = await response.json();

      if (response.ok) {
        setVerificationState({
          status: 'sent',
          message: 'A new verification email has been sent. Please check your inbox.'
        });
      } else {
        throw new Error(result.detail || 'Failed to resend verification email');
      }
    } catch (error) {
      setVerificationState({
        status: 'error',
        message: error.message,
        error: true
      });
    }
  };

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
                <Link to="/login" className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500">
                  Go to Login
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
                <div className="mt-1">
                  <input
                    id="email"
                    name="email"
                    type="email"
                    autoComplete="email"
                    placeholder="Enter your email address"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm mb-4"
                  />
                  <button
                    onClick={handleResendVerification}
                    className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                  >
                    Resend Verification Email
                  </button>
                </div>
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
                <div className="mt-1">
                  <input
                    id="email"
                    name="email"
                    type="email"
                    autoComplete="email"
                    placeholder="Enter your email address"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm mb-4"
                  />
                  <button
                    onClick={handleResendVerification}
                    className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                  >
                    Resend Verification Email
                  </button>
                </div>
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
                <Link to="/login" className="text-primary-600 hover:text-primary-500">
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