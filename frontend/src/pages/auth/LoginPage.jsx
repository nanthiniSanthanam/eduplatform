/**
 * File: frontend/src/pages/auth/LoginPage.jsx
 * Purpose: Login page for user authentication with JWT token support
 * 
 * This component handles:
 * - User login with email and password
 * - JWT token storage after successful authentication
 * - Error display for authentication failures
 * - Redirect to dashboard after login
 * - Remember me functionality
 * - Social login options
 * 
 * Modifications for new backend:
 * 1. Changed from username-based to email-based authentication
 * 2. Added JWT token handling
 * 3. Added support for role-based access control
 * 4. Enhanced error handling for account lockouts
 * 
 * Fields used from backend:
 * - email: User's email address for authentication (previously username)
 * - password: User's password
 */

import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useFormik } from 'formik';
import * as Yup from 'yup';
import FormInput from '../../components/common/FormInput';
import Button from '../../components/common/Button';
import { useAuth } from '../../contexts/AuthContext';

const LoginPage = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [loginError, setLoginError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);

  // Get the return URL from location state or default to dashboard
  const from = location.state?.from?.pathname || '/dashboard';

  const formik = useFormik({
    initialValues: {
      email: '', // Changed from username to email
      password: '',
    },
    validationSchema: Yup.object({
      email: Yup.string()
        .email('Invalid email address')
        .required('Email is required'), // Changed validation to email
      password: Yup.string().required('Password is required'),
    }),
    onSubmit: async (values) => {
      setIsLoading(true);
      setLoginError(null);
      try {
        // Updated to use email instead of username
        const success = await login(values.email, values.password, rememberMe);
        if (success) {
          navigate(from, { replace: true });
        } else {
          setLoginError('Failed to login. Please check your credentials.');
        }
      } catch (error) {
        // Enhanced error handling for account lockouts and other scenarios
        if (error.response && error.response.data) {
          const { detail } = error.response.data;
          if (detail && detail.includes('account is temporarily locked')) {
            setLoginError('Your account is temporarily locked due to multiple failed login attempts. Please try again later.');
          } else if (detail && detail.includes('verify your email')) {
            setLoginError('Please verify your email address before logging in.');
          } else {
            setLoginError(detail || 'Failed to login. Please check your credentials.');
          }
        } else {
          setLoginError('An error occurred. Please try again.');
        }
        console.error('Login error:', error);
      } finally {
        setIsLoading(false);
      }
    },
  });

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
          Sign in to your account
        </h2>
        <p className="mt-2 text-center text-sm text-gray-600">
          Or{' '}
          <Link to="/register" className="font-medium text-primary-600 hover:text-primary-500">
            create a new account
          </Link>
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
          {loginError && (
            <div className="mb-4 bg-red-50 border-l-4 border-red-500 p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-red-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <p className="text-sm text-red-700">{loginError}</p>
                </div>
              </div>
            </div>
          )}
          
          <form className="space-y-6" onSubmit={formik.handleSubmit}>
            {/* Changed from username to email */}
            <FormInput
              label="Email Address"
              name="email"
              type="email" /* Changed input type to email */
              value={formik.values.email}
              onChange={formik.handleChange}
              onBlur={formik.handleBlur}
              error={formik.touched.email && formik.errors.email}
              required
            />

            <FormInput
              label="Password"
              name="password"
              type="password"
              value={formik.values.password}
              onChange={formik.handleChange}
              onBlur={formik.handleBlur}
              error={formik.touched.password && formik.errors.password}
              required
            />

            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <input
                  id="remember-me"
                  name="remember-me"
                  type="checkbox"
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                  checked={rememberMe}
                  onChange={() => setRememberMe(!rememberMe)}
                />
                <label htmlFor="remember-me" className="ml-2 block text-sm text-gray-900">
                  Remember me
                </label>
              </div>

              <div className="text-sm">
                <Link to="/forgot-password" className="font-medium text-primary-600 hover:text-primary-500">
                  Forgot your password?
                </Link>
              </div>
            </div>

            <div>
              <Button
                type="submit"
                fullWidth
                disabled={isLoading}
              >
                {isLoading ? (
                  <span className="flex items-center justify-center">
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Signing in...
                  </span>
                ) : (
                  'Sign in'
                )}
              </Button>
            </div>
          </form>

          <div className="mt-6">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-300"></div>
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-white text-gray-500">
                  Or continue with
                </span>
              </div>
            </div>

            <div className="mt-6 grid grid-cols-2 gap-3">
              <div>
                <a
                  href="#"
                  className="w-full inline-flex justify-center py-2 px-4 border border-gray-300 rounded-md shadow-sm bg-white text-sm font-medium text-gray-500 hover:bg-gray-50"
                >
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
                    <path fillRule="evenodd" d="M10 0C4.477 0 0 4.477 0 10c0 4.42 2.87 8.17 6.84 9.5.5.09.68-.22.68-.48v-1.69c-2.77.6-3.36-1.34-3.36-1.34-.46-1.16-1.11-1.47-1.11-1.47-.9-.61.07-.6.07-.6 1 .07 1.53 1.03 1.53 1.03.9 1.52 2.34 1.08 2.91.83.09-.65.35-1.09.63-1.34-2.22-.25-4.55-1.11-4.55-4.92 0-1.09.39-1.98 1.03-2.68-.1-.25-.45-1.28.1-2.66 0 0 .84-.27 2.75 1.02A9.58 9.58 0 0110 2.8c.85 0 1.72.11 2.5.34 1.91-1.29 2.75-1.02 2.75-1.02.55 1.38.2 2.41.1 2.66.64.7 1.03 1.59 1.03 2.68 0 3.82-2.34 4.67-4.57 4.92.36.31.68.92.68 1.85V19c0 .27.18.58.69.48A10.01 10.01 0 0020 10C20 4.477 15.523 0 10 0z" clipRule="evenodd" />
                  </svg>
                </a>
              </div>

              <div>
                <a
                  href="#"
                  className="w-full inline-flex justify-center py-2 px-4 border border-gray-300 rounded-md shadow-sm bg-white text-sm font-medium text-gray-500 hover:bg-gray-50"
                >
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
                    <path fillRule="evenodd" d="M10 0C4.477 0 0 4.477 0 10c0 5.523 4.477 10 10 10 5.523 0 10-4.477 10-10 0-5.523-4.477-10-10-10zm-1.143 15.714h-.857c-.535 0-.968-.433-.968-.969v-1.942h2.969c.535 0 .968.433.968.969v.969c0 .536-.433.973-.968.973H8.857zm7.914-3.857H7.143c-.535 0-.968-.433-.968-.969V6.857c0-.535.433-.968.968-.968H16.77c.534 0 .967.433.967.968v4.031c0 .536-.433.97-.967.97z" clipRule="evenodd" />
                  </svg>
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;