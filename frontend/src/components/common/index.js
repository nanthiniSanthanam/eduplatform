/**
 * Common Components Index
 * 
 * This file serves as a central export point for all common/reusable components.
 * This pattern provides several benefits:
 * 
 * 1. Simplified Imports: Instead of importing each component individually from its own file,
 *    you can import multiple components from this single entry point:
 *    import { Button, Card, Badge } from '../components/common';
 * 
 * 2. Better Organization: It makes the codebase more organized by providing a clear
 *    catalog of available reusable components.
 * 
 * 3. Easier Maintenance: When components need to be renamed or restructured,
 *    you only need to update the exports here rather than throughout the codebase.
 * 
 * 4. Discoverability: New team members can quickly see what components are available
 *    by looking at this file.
 */

// UI Elements
import Button from './Button';
import Card from './Card';
import Badge from './Badge';
import Avatar from './Avatar';
import Rating from './Rating';
import Alert from './Alert';
import ProgressBar from './ProgressBar';
import Skeleton, { TextSkeleton, CardSkeleton } from './Skeleton';
import Tooltip from './Tooltip';
import AnimatedElement from './AnimatedElement';
import Certificate from './Certificate';
import Container from './Container'; 
import LoadingScreen from './LoadingScreen';
import ResumeButton from './ResumeButton';
import BookmarksList from './BookmarksList';
import Spinner from './Spinner';
import ErrorBoundary from './ErrorBoundary';
// Form Elements
import FormInput from './FormInput';

// Layout Components
import Modal from './Modal';
import Tabs from './Tabs';
import Accordion from './Accordion';
import StepIndicator from './StepIndicator';
import TagInput from './TagInput';
import ResourceCard from './ResourceCard';
import SearchBar from './SearchBar';
import Sidebar from './Sidebar';
import ContentAccessController from './ContentAccessController';
import Dropdown from './Dropdown';
import Pagination from './Pagination';
import ProfileBadge from './ProfileBadge';

// Export individual components
export {
  // UI Elements
  Button,
  Card,
  Container,
  Badge,
  Avatar,
  Rating,
  Alert,
  ProgressBar,
  Skeleton,
  TextSkeleton,
  CardSkeleton,
  Tooltip,
  AnimatedElement,
  Certificate,
  LoadingScreen,
  ResumeButton,
  BookmarksList,
  Spinner,
  ErrorBoundary,
  
  // Form Elements
  FormInput,
  TagInput,
  
  // Layout Components
  Modal,
  Tabs,
  Accordion,
  StepIndicator,
  ResourceCard,
  SearchBar,
  Sidebar,
  ContentAccessController,
  Dropdown,
  Pagination,
  ProfileBadge
};

// Export utility functions
export const getInitials = (name) => {
  if (!name) return '';
  return name
    .split(' ')
    .map(part => part[0])
    .join('')
    .toUpperCase();
};

/**
 * Usage examples:
 * 
 * 1. Import multiple components:
 *    import { Button, Card, Avatar } from '../components/common';
 * 
 * 2. Import a specific component:
 *    import { Button } from '../components/common';
 *    
 * 3. Import with alias:
 *    import { Button as CustomButton } from '../components/common';
 */

export default {
  Alert,
  AnimatedElement,
  Avatar,
  Badge,
  Button,
  Card,
  Container,
  ContentAccessController,
  Dropdown,
  ErrorBoundary,
  FormInput,
  LoadingScreen,
  Modal,
  Pagination,
  ProfileBadge,
  ProgressBar,
  Rating,
  ResourceCard,
  SearchBar,
  Sidebar,
  Skeleton,
  Spinner,
  TagInput,
  Tabs,
  Accordion,
  StepIndicator,
  TextSkeleton,
  CardSkeleton,
  Tooltip,
  Certificate
};