import React, { useState } from 'react';

/**
 * Alert component for displaying notification messages
 * @param {Object} props - Component props
 * @param {string} props.type - Alert type: 'success', 'error', 'warning', 'info'
 * @param {string} props.message - Alert message content
 * @param {boolean} props.dismissible - Whether the alert can be dismissed
 * @param {function} props.onDismiss - Callback when alert is dismissed
 */
const Alert = ({ 
  type = 'info',
  message,
  dismissible = true,
  onDismiss = () => {},
  className = ''
}) => {
  const [visible, setVisible] = useState(true);

  // Color classes based on alert type
  const alertStyles = {
    success: 'bg-green-100 border-green-500 text-green-700',
    error: 'bg-red-100 border-red-500 text-red-700',
    warning: 'bg-yellow-100 border-yellow-500 text-yellow-700',
    info: 'bg-blue-100 border-blue-500 text-blue-700'
  };

  // Icon based on alert type
  const alertIcons = {
    success: (
      <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
      </svg>
    ),
    error: (
      <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
      </svg>
    ),
    warning: (
      <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
        <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
      </svg>
    ),
    info: (
      <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
        <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
      </svg>
    )
  };

  const handleDismiss = () => {
    setVisible(false);
    onDismiss();
  };

  if (!visible) {
    return null;
  }

  return (
    <div className={`border-l-4 p-4 mb-4 rounded ${alertStyles[type]} ${className}`} role="alert">
      <div className="flex items-center">
        <div className="flex-shrink-0 mr-3">
          {alertIcons[type]}
        </div>
        <div className="flex-grow">
          <p className="font-medium">{message}</p>
        </div>
        {dismissible && (
          <button 
            onClick={handleDismiss}
            className="ml-auto -mx-1.5 -my-1.5 bg-transparent text-current p-1.5 rounded-lg focus:ring-2 focus:ring-gray-400 hover:bg-gray-200 inline-flex items-center justify-center"
            aria-label="Close"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          </button>
        )}
      </div>
    </div>
  );
};

// Named export
export { Alert };

// Default export
export default Alert;