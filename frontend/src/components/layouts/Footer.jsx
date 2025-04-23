import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

const Footer = () => {
  const { currentUser } = useAuth();
  const username = 'nanthiniSanthanam'; // Default username
  
  // Dynamic current date/time
  const [currentDateTime, setCurrentDateTime] = useState('');
  
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
    
    return () => clearInterval(timer);
  }, []);
  
  const currentYear = new Date().getFullYear();
  
  return (
    <footer className="bg-gray-900 text-white pt-16 pb-8 w-full">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-10 mb-16">
          {/* Column 1: Company Info */}
          <div className="lg:col-span-2">
            <div className="flex items-center mb-6 group">
              <div className="h-10 w-10 bg-white rounded-xl flex items-center justify-center text-primary-600 font-bold text-lg mr-3 shadow-md group-hover:bg-primary-500 group-hover:text-white transition-all">ST</div>
              <span className="text-2xl font-bold text-white font-display tracking-tight group-hover:text-primary-300 transition-colors">SoftTech Solutions</span>
            </div>
            <p className="text-gray-400 mb-6 max-w-md">
              Our mission is to democratize access to high-quality education by providing an integrated platform that combines comprehensive learning resources, interactive tools, and community collaboration.
            </p>
            <div className="flex space-x-4 mb-8">
              <a href="#" className="w-10 h-10 bg-gray-800 hover:bg-primary-600 rounded-full flex items-center justify-center text-gray-400 hover:text-white transition-colors">
                <i className="fa-brands fa-facebook-f"></i>
              </a>
              <a href="#" className="w-10 h-10 bg-gray-800 hover:bg-primary-600 rounded-full flex items-center justify-center text-gray-400 hover:text-white transition-colors">
                <i className="fa-brands fa-twitter"></i>
              </a>
              <a href="#" className="w-10 h-10 bg-gray-800 hover:bg-primary-600 rounded-full flex items-center justify-center text-gray-400 hover:text-white transition-colors">
                <i className="fa-brands fa-linkedin-in"></i>
              </a>
              <a href="#" className="w-10 h-10 bg-gray-800 hover:bg-primary-600 rounded-full flex items-center justify-center text-gray-400 hover:text-white transition-colors">
                <i className="fa-brands fa-instagram"></i>
              </a>
              <a href="#" className="w-10 h-10 bg-gray-800 hover:bg-primary-600 rounded-full flex items-center justify-center text-gray-400 hover:text-white transition-colors">
                <i className="fa-brands fa-youtube"></i>
              </a>
            </div>
          </div>
          
          {/* Column 2: Quick Links */}
          <div>
            <h3 className="text-lg font-semibold mb-6 text-white">Learning Platform</h3>
            <ul className="space-y-4">
              <li><Link to="/" className="text-gray-400 hover:text-white transition-colors inline-block">Home</Link></li>
              <li><Link to="/courses" className="text-gray-400 hover:text-white transition-colors inline-block">Courses</Link></li>
              <li><Link to="/virtual-lab" className="text-gray-400 hover:text-white transition-colors inline-block">Virtual Labs</Link></li>
              <li><Link to="/learning-paths" className="text-gray-400 hover:text-white transition-colors inline-block">Learning Paths</Link></li>
              <li><Link to="/community" className="text-gray-400 hover:text-white transition-colors inline-block">Community</Link></li>
              <li><Link to="/blog" className="text-gray-400 hover:text-white transition-colors inline-block">Blog</Link></li>
            </ul>
          </div>
          
          {/* Column 3: Resources */}
          <div>
            <h3 className="text-lg font-semibold mb-6 text-white">Resources</h3>
            <ul className="space-y-4">
              <li><Link to="/help" className="text-gray-400 hover:text-white transition-colors inline-block">Help Center</Link></li>
              <li><Link to="/docs" className="text-gray-400 hover:text-white transition-colors inline-block">Documentation</Link></li>
              <li><Link to="/api-reference" className="text-gray-400 hover:text-white transition-colors inline-block">API Reference</Link></li>
              <li><Link to="/tutorials" className="text-gray-400 hover:text-white transition-colors inline-block">Tutorials</Link></li>
              <li><Link to="/webinars" className="text-gray-400 hover:text-white transition-colors inline-block">Webinars</Link></li>
              <li><Link to="/research" className="text-gray-400 hover:text-white transition-colors inline-block">Research Papers</Link></li>
            </ul>
          </div>
          
          {/* Column 4: Legal */}
          <div>
            <h3 className="text-lg font-semibold mb-6 text-white">Company</h3>
            <ul className="space-y-4">
              <li><Link to="/about" className="text-gray-400 hover:text-white transition-colors inline-block">About Us</Link></li>
              <li><Link to="/careers" className="text-gray-400 hover:text-white transition-colors inline-block">Careers</Link></li>
              <li><Link to="/partners" className="text-gray-400 hover:text-white transition-colors inline-block">Partners</Link></li>
              <li><Link to="/terms" className="text-gray-400 hover:text-white transition-colors inline-block">Terms of Service</Link></li>
              <li><Link to="/privacy" className="text-gray-400 hover:text-white transition-colors inline-block">Privacy Policy</Link></li>
              <li><Link to="/contact" className="text-gray-400 hover:text-white transition-colors inline-block">Contact Us</Link></li>
            </ul>
          </div>
        </div>
        
        {/* Newsletter - Full width container */}
        <div className="border-t border-gray-800 pt-10 pb-8 mb-8 w-full">
          <div className="max-w-xl mx-auto text-center">
            <h3 className="text-xl font-semibold mb-4 text-white">Stay Updated with SoftTech</h3>
            <p className="text-gray-400 mb-6">Get the latest updates, learning resources, and special offers delivered directly to your inbox.</p>
            <form className="flex flex-col sm:flex-row gap-3">
              <input type="email" placeholder="Your email address" className="flex-grow px-4 py-3 rounded-xl bg-gray-800 text-white border border-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all" />
              <button type="submit" className="px-6 py-3 bg-primary-600 hover:bg-primary-700 rounded-xl font-medium transition-colors shadow-sm text-white">Subscribe</button>
            </form>
          </div>
        </div>
        
        {/* Copyright - Updated with current date, time, and username */}
        <div className="border-t border-gray-800 pt-8 flex flex-col md:flex-row justify-between items-center w-full">
          <p className="text-gray-500 text-sm mb-4 md:mb-0">
            © {currentYear} SoftTech Solutions. All rights reserved.
          </p>
          <p className="text-gray-500 text-sm">
            Current Date and Time (UTC): {currentDateTime} • User: {username}
          </p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;