/**
 * File: frontend/src/utils/transformData.js
 * Purpose: Utility functions for transforming data between backend and frontend
 * 
 * These functions handle the conversion between snake_case (backend) and
 * camelCase (frontend) naming conventions, ensuring compatibility between
 * the two systems.
 */

import camelcaseKeys from 'camelcase-keys';
import snakecaseKeys from 'snakecase-keys';

/**
 * Transform backend data (snake_case) to frontend format (camelCase)
 * @param {Object|Array} data - Data from backend API
 * @returns {Object|Array} - Transformed data in camelCase
 */
export const snakeToCamel = (data) => {
  return camelcaseKeys(data, { deep: true });
};

/**
 * Transform frontend data (camelCase) to backend format (snake_case)
 * @param {Object|Array} data - Data to send to backend API
 * @returns {Object|Array} - Transformed data in snake_case
 */
export const camelToSnake = (data) => {
  return snakecaseKeys(data, { deep: true });
};

/**
 * Format date to display format
 * @param {string} dateString - ISO date string from backend
 * @returns {string} - Formatted date string
 */
export const formatDate = (dateString) => {
  if (!dateString) return '';
  
  const date = new Date(dateString);
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  }).format(date);
};

/**
 * Format price to display format
 * @param {number} price - Price value
 * @returns {string} - Formatted price string
 */
export const formatPrice = (price) => {
  if (price === 0) return 'Free';
  
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD'
  }).format(price);
};

/**
 * Format duration for display
 * @param {number} minutes - Duration in minutes
 * @returns {string} - Formatted duration string
 */
export const formatDuration = (minutes) => {
  if (!minutes) return '';
  
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  
  if (hours === 0) {
    return `${mins} min${mins !== 1 ? 's' : ''}`;
  } else if (mins === 0) {
    return `${hours} hour${hours !== 1 ? 's' : ''}`;
  } else {
    return `${hours} hour${hours !== 1 ? 's' : ''} ${mins} min${mins !== 1 ? 's' : ''}`;
  }
};