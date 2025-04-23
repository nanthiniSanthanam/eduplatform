import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

const Header = () => {
  const { currentUser, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [isOpen, setIsOpen] = useState(false);
  const [isScrolled, setIsScrolled] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  
  // Dynamic date and time
  const [currentDateTime, setCurrentDateTime] = useState('');
  const username = 'nanthiniSanthanam'; // Default username
  
  // Generate initials for avatar
  const getInitials = (name) => {
    if (!name) return 'US';
    const nameParts = name.split(' ');
    if (nameParts.length >= 2) {
      return `${nameParts[0].charAt(0)}${nameParts[1].charAt(0)}`;
    }
    return name.substring(0, 2).toUpperCase();
  };

  useEffect(() => {
    // Function to format date in YYYY-MM-DD HH:MM:SS format
    const formatDate = (date) => {
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const day = String(date.getDate()).padStart(2, '0');
      const hours = String(date.getHours()).padStart(2, '0');
      const minutes = String(date.getMinutes()).padStart(2, '0');
      const seconds = String(date.getSeconds()).padStart(2, '0');
      
      return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
    };

    // Update date and time initially
    setCurrentDateTime(formatDate(new Date()));
    
    // Update date and time every minute
    const timer = setInterval(() => {
      setCurrentDateTime(formatDate(new Date()));
    }, 60000);

    const handleScroll = () => {
      setIsScrolled(window.pageYOffset > 50);
    };

    window.addEventListener('scroll', handleScroll);
    
    return () => {
      clearInterval(timer);
      window.removeEventListener('scroll', handleScroll);
    };
  }, []);

  const handleLogout = async () => {
    try {
      await logout();
      navigate('/login');
    } catch (error) {
      console.error('Failed to log out', error);
    }
  };

  const isActive = (path) => {
    if (path === '/' && location.pathname !== '/') return false;
    return location.pathname.startsWith(path);
  };

  // Create safe initials for the avatar
  const userInitials = getInitials(username);

  return (
    <>
      {/* Current UTC Time and User Info Banner - Responsive full width */}
      <div className="hidden md:block bg-gray-900 text-gray-300 text-xs py-1 w-full">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 flex justify-between items-center">
          <div>Current Date and Time (UTC): <span className="font-medium">{currentDateTime}</span></div>
          <div>User: <span className="font-medium">{username}</span></div>
        </div>
      </div>

      {/* Header with Navigation - Full width with container inside */}
      <header 
        className={`sticky top-0 z-50 w-full transition-all duration-300 ease-in-out ${
          isScrolled ? 'py-2 bg-white/90 backdrop-blur-md shadow-soft' : 'py-4 bg-white'
        }`}
      >
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 flex justify-between items-center">
          {/* Logo with enhanced styling */}
          <Link to="/" className="flex items-center group">
            <div className="h-10 w-10 bg-primary-500 rounded-xl flex items-center justify-center text-white font-bold text-lg mr-3 shadow-md group-hover:bg-primary-600 transition-all">ST</div>
            <span className="text-xl md:text-2xl font-bold text-gray-900 font-display tracking-tight group-hover:text-primary-500 transition-colors">SoftTech Solutions</span>
          </Link>
          
          {/* Mobile Menu Button - Refined styling */}
          <button 
            onClick={() => setIsOpen(!isOpen)} 
            className="md:hidden text-gray-700 hover:text-primary-500 focus:outline-none transition-colors"
          >
            <i className={`fa-solid ${isOpen ? 'fa-xmark text-lg' : 'fa-bars text-lg'}`}></i>
          </button>
          
          {/* Desktop Navigation - Enhanced with subtle hover effects */}
          <nav className="hidden md:flex items-center space-x-1">
            <Link to="/" className={`px-3 py-2 rounded-lg font-medium ${isActive('/') ? 'text-primary-500' : 'text-gray-700 hover:bg-primary-50 hover:text-primary-500 transition-colors'}`}>
              Home
            </Link>
            <Link to="/courses" className={`px-3 py-2 rounded-lg font-medium ${isActive('/courses') ? 'text-primary-500' : 'text-gray-700 hover:bg-primary-50 hover:text-primary-500 transition-colors'}`}>
              Explore
            </Link>
            <Link to="/learning-paths" className={`px-3 py-2 rounded-lg font-medium ${isActive('/learning') ? 'text-primary-500' : 'text-gray-700 hover:bg-primary-50 hover:text-primary-500 transition-colors'}`}>
              Learn
            </Link>
            <Link to="/virtual-lab" className={`px-3 py-2 rounded-lg font-medium ${isActive('/virtual-lab') ? 'text-primary-500' : 'text-gray-700 hover:bg-primary-50 hover:text-primary-500 transition-colors'}`}>
              Practice
            </Link>
            <Link to="/community" className={`px-3 py-2 rounded-lg font-medium ${isActive('/community') ? 'text-primary-500' : 'text-gray-700 hover:bg-primary-50 hover:text-primary-500 transition-colors'}`}>
              Community
            </Link>
            <Link to="/resources" className={`px-3 py-2 rounded-lg font-medium ${isActive('/resources') ? 'text-primary-500' : 'text-gray-700 hover:bg-primary-50 hover:text-primary-500 transition-colors'}`}>
              Resources
            </Link>
            
            {/* Search Box - Enhanced with premium styling */}
            <div className="relative ml-4">
              <input type="text" placeholder="Search courses..." className="w-64 pl-10 pr-4 py-2.5 rounded-xl bg-gray-100 border-none focus:bg-white focus:ring-2 focus:ring-primary-300 transition-all text-sm" />
              <i className="fa-solid fa-search absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400"></i>
            </div>
            
            {/* User Menu (logged in state) - Enhanced with premium styling */}
            <div className="relative ml-3">
              <button 
                onClick={() => setUserMenuOpen(!userMenuOpen)} 
                className="flex items-center space-x-2 group"
              >
                <div className="h-9 w-9 rounded-full bg-primary-500 flex items-center justify-center text-white shadow-sm overflow-hidden border-2 border-white group-hover:border-primary-100 transition-all">
                  {/* Use inline style for colored background instead of UI Avatars API */}
                  <div className="h-full w-full flex items-center justify-center bg-primary-500 text-white">
                    {userInitials}
                  </div>
                </div>
                <span className="text-sm font-medium text-gray-700 group-hover:text-primary-500 hidden lg:inline-block transition-colors">
                  {username}
                </span>
                <i className="fa-solid fa-chevron-down text-xs text-gray-400 group-hover:text-primary-500 transition-colors"></i>
              </button>
              
              {/* Dropdown Menu - More premium styling */}
              {userMenuOpen && (
                <div className="absolute right-0 mt-3 w-56 bg-white rounded-xl shadow-soft py-2 border border-gray-100 focus:outline-none z-50">
                  <div className="px-4 py-2 border-b border-gray-100">
                    <p className="text-sm font-medium text-gray-900">{username}</p>
                    <p className="text-xs text-gray-500">user@example.com</p>
                  </div>
                  <Link to="/dashboard" className="block px-4 py-2.5 text-sm text-gray-700 hover:bg-gray-50 hover:text-primary-500" onClick={() => setUserMenuOpen(false)}>
                    My Dashboard
                  </Link>
                  <Link to="/profile" className="block px-4 py-2.5 text-sm text-gray-700 hover:bg-gray-50 hover:text-primary-500" onClick={() => setUserMenuOpen(false)}>
                    Profile
                  </Link>
                  <Link to="/settings" className="block px-4 py-2.5 text-sm text-gray-700 hover:bg-gray-50 hover:text-primary-500" onClick={() => setUserMenuOpen(false)}>
                    Settings
                  </Link>
                  <div className="border-t border-gray-100 my-1"></div>
                  <button 
                    onClick={handleLogout}
                    className="block w-full text-left px-4 py-2.5 text-sm text-gray-700 hover:bg-gray-50 hover:text-primary-500"
                  >
                    Sign out
                  </button>
                </div>
              )}
            </div>
          </nav>
        </div>
        
        {/* Mobile Menu - Full width */}
        {isOpen && (
          <div className="md:hidden bg-white border-t mt-2 shadow-md w-full">
            <div className="px-4 pt-4 pb-5 space-y-3">
              <Link to="/" className={`block px-4 py-3 rounded-lg font-medium ${isActive('/') ? 'text-primary-500 bg-primary-50' : 'text-gray-700 hover:bg-primary-50 hover:text-primary-500'}`} onClick={() => setIsOpen(false)}>
                Home
              </Link>
              <Link to="/courses" className={`block px-4 py-3 rounded-lg font-medium ${isActive('/courses') ? 'text-primary-500 bg-primary-50' : 'text-gray-700 hover:bg-primary-50 hover:text-primary-500'}`} onClick={() => setIsOpen(false)}>
                Explore
              </Link>
              <Link to="/learning-paths" className={`block px-4 py-3 rounded-lg font-medium ${isActive('/learning') ? 'text-primary-500 bg-primary-50' : 'text-gray-700 hover:bg-primary-50 hover:text-primary-500'}`} onClick={() => setIsOpen(false)}>
                Learn
              </Link>
              <Link to="/virtual-lab" className={`block px-4 py-3 rounded-lg font-medium ${isActive('/virtual-lab') ? 'text-primary-500 bg-primary-50' : 'text-gray-700 hover:bg-primary-50 hover:text-primary-500'}`} onClick={() => setIsOpen(false)}>
                Practice
              </Link>
              <Link to="/community" className={`block px-4 py-3 rounded-lg font-medium ${isActive('/community') ? 'text-primary-500 bg-primary-50' : 'text-gray-700 hover:bg-primary-50 hover:text-primary-500'}`} onClick={() => setIsOpen(false)}>
                Community
              </Link>
              <Link to="/resources" className={`block px-4 py-3 rounded-lg font-medium ${isActive('/resources') ? 'text-primary-500 bg-primary-50' : 'text-gray-700 hover:bg-primary-50 hover:text-primary-500'}`} onClick={() => setIsOpen(false)}>
                Resources
              </Link>
            </div>
            
            {/* Mobile Search - Enhanced styling */}
            <div className="px-4 py-4 border-t border-gray-100">
              <div className="relative">
                <input type="text" placeholder="Search courses..." className="w-full pl-10 pr-4 py-3 rounded-lg bg-gray-100 border-none focus:ring-2 focus:ring-primary-300 transition-all" />
                <i className="fa-solid fa-search absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400"></i>
              </div>
            </div>
            
            {/* Mobile User Menu - Enhanced styling */}
            <div className="px-4 py-4 border-t border-gray-100">
              <div className="flex items-center">
                <div className="h-10 w-10 rounded-full bg-primary-500 flex items-center justify-center text-white shadow-sm overflow-hidden mr-3">
                  {/* Replace avatar URL with inline style */}
                  <div className="h-full w-full flex items-center justify-center bg-primary-500 text-white">
                    {userInitials}
                  </div>
                </div>
                <div>
                  <div className="text-sm font-medium text-gray-900">{username}</div>
                  <div className="text-xs text-gray-500">user@example.com</div>
                </div>
              </div>
              <div className="mt-4 space-y-2">
                <Link to="/dashboard" className="block px-4 py-2.5 rounded-lg text-gray-700 hover:bg-primary-50 hover:text-primary-500" onClick={() => setIsOpen(false)}>
                  My Dashboard
                </Link>
                <Link to="/profile" className="block px-4 py-2.5 rounded-lg text-gray-700 hover:bg-primary-50 hover:text-primary-500" onClick={() => setIsOpen(false)}>
                  Profile
                </Link>
                <Link to="/settings" className="block px-4 py-2.5 rounded-lg text-gray-700 hover:bg-primary-50 hover:text-primary-500" onClick={() => setIsOpen(false)}>
                  Settings
                </Link>
                <button 
                  onClick={handleLogout}
                  className="block w-full text-left px-4 py-2.5 rounded-lg text-gray-700 hover:bg-primary-50 hover:text-primary-500"
                >
                  Sign out
                </button>
              </div>
            </div>
            
            {/* Mobile Time & User Info - Updated with current date and time */}
            <div className="px-4 py-3 bg-gray-50 text-xs text-gray-500 border-t border-gray-100">
              <p>Current Date and Time (UTC): {currentDateTime}</p>
              <p>User: {username}</p>
            </div>
          </div>
        )}
      </header>
    </>
  );
};

export default Header;