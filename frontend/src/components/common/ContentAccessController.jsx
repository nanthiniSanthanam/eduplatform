/**
 * File: frontend/src/components/common/ContentAccessController.jsx
 * Purpose: Control content display based on user access level for educational platform
 * 
 * This component manages tiered content access in the educational platform:
 * - Shows basic content to unregistered users (previews)
 * - Shows intermediate content to registered users (standard lessons)
 * - Shows advanced content to paid premium users (premium lessons with additional resources)
 * 
 * Access is determined through the AuthContext's getAccessLevel function.
 * The component renders appropriate content based on the user's access level
 * and displays upgrade prompts for content the user cannot access.
 * 
 * Features:
 * - Automatic access level determination through AuthContext
 * - Conditional rendering based on access level
 * - Upgrade prompts with links to register or pricing page
 * - Customizable upgrade messages
 * 
 * Usage example:
 * <ContentAccessController
 *   requiredLevel="intermediate"
 *   basicContent={<p>Preview content</p>}
 *   intermediateContent={<p>Standard content</p>}
 *   advancedContent={<p>Premium content</p>}
 *   upgradeMessage="Upgrade to see full content"
 * />
 * 
 * Variables that may need modification:
 * - DEFAULT_UPGRADE_MESSAGE: Default message shown when content is locked
 * - ACCESS_LEVELS: Object containing the tier level constants (should match backend)
 * - ACCESS_HIERARCHY: Numeric values defining the hierarchy of access levels
 * 
 * Created by: Professor Santhanam
 * Last updated: 2025-04-27
 */

import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import Button from './Button';

// Default message shown when content is locked - customize this if needed
const DEFAULT_UPGRADE_MESSAGE = "Upgrade your account to access this content";

// Access level definitions - these match the lesson.access_level values in the database
// IMPORTANT: These must match the backend Lesson.ACCESS_LEVEL_CHOICES values
const ACCESS_LEVELS = {
  BASIC: 'basic',         // Unregistered users
  INTERMEDIATE: 'intermediate',  // Registered users
  ADVANCED: 'advanced'    // Paid users
};

// Level hierarchy - determines which user can access which content
// Higher values can access content of lower values
const ACCESS_HIERARCHY = {
  [ACCESS_LEVELS.BASIC]: 0,
  [ACCESS_LEVELS.INTERMEDIATE]: 1,
  [ACCESS_LEVELS.ADVANCED]: 2
};

/**
 * ContentAccessController component
 * @param {React.ReactNode} basicContent - Content visible to all users (unregistered and above)
 * @param {React.ReactNode} intermediateContent - Content visible to registered users (free and paid)
 * @param {React.ReactNode} advancedContent - Content visible only to paid premium users
 * @param {string} requiredLevel - The minimum access level required ('basic', 'intermediate', 'advanced')
 * @param {string} upgradeMessage - Custom message to show when content is locked
 */
const ContentAccessController = ({ 
  basicContent, 
  intermediateContent, 
  advancedContent,
  requiredLevel = ACCESS_LEVELS.BASIC,
  upgradeMessage = DEFAULT_UPGRADE_MESSAGE
}) => {
  // Get authentication context from AuthContext provider
  const { currentUser, isAuthenticated, getAccessLevel } = useAuth();
  
  // Get the user's current access level
  // This will be 'basic', 'intermediate', or 'advanced'
  const userAccessLevel = getAccessLevel ? getAccessLevel() : 
                          (isAuthenticated() ? ACCESS_LEVELS.INTERMEDIATE : ACCESS_LEVELS.BASIC);
  
  // Convert access levels to numeric values for comparison
  const userAccessValue = ACCESS_HIERARCHY[userAccessLevel];
  const requiredAccessValue = ACCESS_HIERARCHY[requiredLevel];
  
  // Check if user can access the content (user level >= required level)
  const canAccess = userAccessValue >= requiredAccessValue;
  
  // If user doesn't have access, show upgrade prompt
  if (!canAccess) {
    return (
      <div className="border border-gray-200 rounded-md p-6 text-center">
        {/* Lock icon */}
        <div className="mb-4">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
        </div>
        
        {/* Content locked message */}
        <h3 className="text-lg font-medium text-gray-900 mb-2">Content Locked</h3>
        <p className="text-gray-500 mb-4">{upgradeMessage}</p>
        
        {/* Show different prompts based on user authentication status */}
        {!isAuthenticated() ? (
          // For unregistered users, show register/login options
          <div className="space-y-2">
            <Link to="/register">
              <Button color="primary" fullWidth>Register for free</Button>
            </Link>
            <p className="text-sm text-gray-500">
              Already have an account? <Link to="/login" className="text-primary-600">Sign in</Link>
            </p>
          </div>
        ) : userAccessLevel === ACCESS_LEVELS.INTERMEDIATE ? (
          // For registered free users, show upgrade option
          <Link to="/pricing">
            <Button color="primary" fullWidth>Upgrade Now</Button>
          </Link>
        ) : (
          // For any other case (should rarely happen)
          <p className="text-sm text-gray-500">
            Please contact support if you believe you should have access to this content.
          </p>
        )}
      </div>
    );
  }
  
  // If user has access, return the appropriate content based on access level
  if (requiredLevel === ACCESS_LEVELS.ADVANCED && advancedContent) {
    // Advanced content for premium users
    return advancedContent;
  } else if ((requiredLevel === ACCESS_LEVELS.INTERMEDIATE || userAccessLevel === ACCESS_LEVELS.INTERMEDIATE) 
              && intermediateContent) {
    // Intermediate content for registered users (or advanced users viewing intermediate content)
    return intermediateContent;
  } else {
    // Basic content for everyone else
    return basicContent;
  }
};

export default ContentAccessController;