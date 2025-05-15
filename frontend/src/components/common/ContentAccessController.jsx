/**
 * File: frontend/src/components/common/ContentAccessController.jsx
 * Date: 2025-05-15 15:22:01
 * Modified: Security & logic fixes based on code review
 * Purpose: Control content display based on user access level
 */

import React from 'react';
import PropTypes from 'prop-types';
import { Link } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import DOMPurify from 'dompurify';

// Define access levels internally since accessLevels.js doesn't exist
const ACCESS_LEVELS = {
  BASIC: 'basic',
  INTERMEDIATE: 'intermediate',
  ADVANCED: 'advanced'
};

// Default message shown when content is locked
const DEFAULT_UPGRADE_MESSAGE = "Upgrade your account to access this premium content";

/**
 * Controls access to content based on the user's access level.
 * Handles content visibility according to subscription tier.
 */
export default function ContentAccessController({
  requiredLevel = ACCESS_LEVELS.BASIC,
  isLoggedIn,
  userAccessLevel,
  basicContent,
  content,
  upgradeMessage,
  children
}) {
  // Use auth context values or provided props
  const auth = useAuth();
  const effectiveIsLoggedIn = isLoggedIn ?? auth?.isAuthenticated ?? false;
  
  // Use provided userAccessLevel or fetch from auth context
  const effectiveUserAccessLevel = 
    userAccessLevel ?? 
    auth?.userAccessLevel ?? 
    (auth?.getAccessLevel?.() || ACCESS_LEVELS.BASIC);
  
  // Normalize required level (default to BASIC if invalid)
  const normalizedRequiredLevel = 
    Object.values(ACCESS_LEVELS).includes(requiredLevel) 
      ? requiredLevel 
      : ACCESS_LEVELS.BASIC;

  // For development debugging only
  if (process.env.NODE_ENV === 'development') {
    console.debug('ContentAccessController:', { 
      requiredLevel: normalizedRequiredLevel, 
      isLoggedIn: effectiveIsLoggedIn, 
      userAccessLevel: effectiveUserAccessLevel
    });
  }

  // BASIC content - accessible to everyone
  if (normalizedRequiredLevel === ACCESS_LEVELS.BASIC) {
    return (
      children ??
      (content && (
        <div
          className="prose max-w-none"
          dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(content) }}
        />
      ))
    );
  }

  // Not logged in users see login prompt for any gated content
  if (!effectiveIsLoggedIn) {
    // If basicContent is a string (HTML), sanitize it
    const sanitizedBasicContent = typeof basicContent === 'string'
      ? <div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(basicContent) }} />
      : basicContent;
    
    return sanitizedBasicContent || (
      <div className="bg-primary-50 border border-primary-200 rounded-lg p-4 my-4">
        <h3 className="font-semibold text-primary-800 mb-1">Login Required</h3>
        <p className="text-primary-700 mb-3">Please sign in to access this content.</p>
        <Link 
          to="/login" 
          className="inline-flex items-center px-3 py-1.5 border border-primary-300 text-sm font-medium rounded-md text-primary-800 bg-primary-100 hover:bg-primary-200"
        >
          Sign In
        </Link>
      </div>
    );
  }

  // For INTERMEDIATE content with logged-in users, show the content
  if (normalizedRequiredLevel === ACCESS_LEVELS.INTERMEDIATE) {
    return (
      children ??
      (content && (
        <div
          className="prose max-w-none"
          dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(content) }}
        />
      ))
    );
  }

  // For ADVANCED content with non-premium users
  if (normalizedRequiredLevel === ACCESS_LEVELS.ADVANCED) {
    if (effectiveUserAccessLevel !== ACCESS_LEVELS.ADVANCED) {
      // If basicContent is a string (HTML), sanitize it
      const sanitizedBasicContent = typeof basicContent === 'string'
        ? <div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(basicContent) }} />
        : basicContent;
      
      return sanitizedBasicContent || (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 my-4">
          <h3 className="font-semibold text-amber-800 mb-1">Premium Content</h3>
          <p className="text-amber-700 mb-3">{upgradeMessage || DEFAULT_UPGRADE_MESSAGE}</p>
          <Link 
            to="/pricing" 
            className="inline-flex items-center px-3 py-1.5 border border-amber-300 text-sm font-medium rounded-md text-amber-800 bg-amber-100 hover:bg-amber-200"
          >
            Upgrade Subscription
          </Link>
        </div>
      );
    }
    // Premium user with advanced content - fall through to show content
  }

  // Default case - show content
  return (
    children ??
    (content && (
      <div
        className="prose max-w-none"
        dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(content) }}
      />
    ))
  );
}

ContentAccessController.propTypes = {
  requiredLevel: PropTypes.oneOf(Object.values(ACCESS_LEVELS)),
  isLoggedIn: PropTypes.bool,
  userAccessLevel: PropTypes.oneOf(Object.values(ACCESS_LEVELS)),
  basicContent: PropTypes.node,
  content: PropTypes.string,
  upgradeMessage: PropTypes.string,
  children: PropTypes.node
};