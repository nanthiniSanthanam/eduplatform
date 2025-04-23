import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import MainLayout from '../components/layouts/MainLayout';
import CourseList from '../components/courses/CourseList';
import BlogPostList from '../components/blog/BlogPostList';
import TestimonialList from '../components/testimonials/TestimonialList';

const HomePage = () => {
  // Dynamic date and time - keep for reference
  const [currentDateTime, setCurrentDateTime] = useState('');
  
  useEffect(() => {
    // Function to format date
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

    // Reveal animations on scroll
    const revealElements = document.querySelectorAll('.reveal');
    
    const revealOnScroll = () => {
      for (let i = 0; i < revealElements.length; i++) {
        const windowHeight = window.innerHeight;
        const revealTop = revealElements[i].getBoundingClientRect().top;
        const revealPoint = 150;
        
        if (revealTop < windowHeight - revealPoint) {
          revealElements[i].classList.add('active');
        }
      }
    };
    
    window.addEventListener('scroll', revealOnScroll);
    
    // Call once to reveal elements that are already visible
    revealOnScroll();
    
    // Back to Top button functionality
    const handleBackToTopVisibility = () => {
      const backToTopButton = document.getElementById('back-to-top');
      if (backToTopButton) {
        if (window.scrollY > 300) {
          backToTopButton.classList.remove('opacity-0', 'invisible');
          backToTopButton.classList.add('opacity-100', 'visible');
        } else {
          backToTopButton.classList.add('opacity-0', 'invisible');
          backToTopButton.classList.remove('opacity-100', 'visible');
        }
      }
    };
    
    window.addEventListener('scroll', handleBackToTopVisibility);
    handleBackToTopVisibility(); // Initial check
    
    const handleBackToTopClick = () => {
      window.scrollTo({
        top: 0,
        behavior: 'smooth'
      });
    };
    
    const backToTopButton = document.getElementById('back-to-top');
    if (backToTopButton) {
      backToTopButton.addEventListener('click', handleBackToTopClick);
    }
    
    // Cleanup event listeners
    return () => {
      clearInterval(timer);
      window.removeEventListener('scroll', revealOnScroll);
      window.removeEventListener('scroll', handleBackToTopVisibility);
      
      if (backToTopButton) {
        backToTopButton.removeEventListener('click', handleBackToTopClick);
      }
    };
  }, []);

  return (
    <MainLayout>
      {/* Hero Section - Enhanced premium styling */}
      <section className="hero-gradient text-white py-16 md:py-24 lg:py-32 relative w-full">
        {/* Decorative Elements */}
        <div className="absolute top-1/2 right-5 w-64 h-64 bg-white/10 rounded-full filter blur-3xl"></div>
        <div className="absolute top-1/3 left-10 w-48 h-48 bg-white/5 rounded-full filter blur-2xl"></div>
        
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row items-center">
            <div className="w-full md:w-1/2 mb-12 md:mb-0 animate-fade-in-up">
              {/* Mission-aligned heading */}
              <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold mb-6 leading-tight font-display">Your Journey to Knowledge and Excellence</h1>
              <p className="text-xl md:text-2xl mb-8 text-blue-100 max-w-lg opacity-90 font-light">Discover a learning ecosystem where knowledge, innovation, and community converge to empower your educational journey.</p>
              <div className="flex flex-wrap gap-4">
                <Link to="/register" className="btn-premium bg-secondary-500 hover:bg-secondary-600 text-white">
                  Start Your Journey
                </Link>
                <Link to="/courses" className="btn-premium bg-white/10 backdrop-blur-sm hover:bg-white/20 text-white border border-white/20">
                  Explore Learning Paths
                </Link>
              </div>
              
              {/* Trust indicators with enhanced styling */}
              <div className="mt-8 md:mt-12 flex items-center space-x-5">
                <div className="flex -space-x-3">
                  <div className="w-8 h-8 rounded-full border-2 border-white bg-primary-500 flex items-center justify-center text-white text-xs">
                    JD
                  </div>
                  <div className="w-8 h-8 rounded-full border-2 border-white bg-tertiary-500 flex items-center justify-center text-white text-xs">
                    SK
                  </div>
                  <div className="w-8 h-8 rounded-full border-2 border-white bg-secondary-500 flex items-center justify-center text-white text-xs">
                    AM
                  </div>
                  <div className="w-8 h-8 rounded-full bg-white/10 backdrop-blur-sm border-2 border-white flex items-center justify-center text-xs font-medium">
                    500k+
                  </div>
                </div>
                <div className="text-sm">
                  <div className="font-medium">Trusted by 500,000+ learners</div>
                  <div className="text-blue-200 flex items-center">
                    <div className="flex text-yellow-400">
                      <i className="fas fa-star"></i>
                      <i className="fas fa-star"></i>
                      <i className="fas fa-star"></i>
                      <i className="fas fa-star"></i>
                      <i className="fas fa-star-half-alt"></i>
                    </div>
                    <span className="ml-2">4.8/5 satisfaction rate</span>
                  </div>
                </div>
              </div>
            </div>
            
            {/* Hero image with premium styling */}
            <div className="w-full md:w-1/2 flex justify-center">
              <div className="relative w-full max-w-md mx-auto">
                {/* Premium shadow effects */}
                <div className="absolute -inset-1 bg-gradient-to-r from-primary-300 to-secondary-300 rounded-2xl blur-xl opacity-30"></div>
                <div className="relative">
                  {/* Replace placeholder with colored div */}
                  <div className="rounded-2xl shadow-xl h-80 md:h-96 lg:h-[500px] w-full max-w-full bg-gray-100 flex items-center justify-center">
                    <div className="text-gray-500 text-lg font-medium">Interactive Learning Platform</div>
                  </div>
                  
                  {/* Floating UI elements for depth - visible only on larger screens */}
                  <div className="hidden md:block absolute -top-6 -right-6 glass-effect rounded-xl p-4 shadow-lg rotate-3">
                    <div className="flex items-center space-x-2">
                      <div className="w-10 h-10 rounded-full bg-secondary-500 flex items-center justify-center text-white">
                        <i className="fas fa-graduation-cap"></i>
                      </div>
                      <div>
                        <p className="text-white font-medium">Certificate Earned!</p>
                        <p className="text-white/70 text-xs">Web Development</p>
                      </div>
                    </div>
                  </div>
                  
                  <div className="hidden md:block absolute -bottom-6 -left-6 glass-effect rounded-xl p-4 shadow-lg -rotate-2">
                    <div className="flex items-center space-x-2">
                      <div className="w-10 h-10 rounded-full bg-tertiary-500 flex items-center justify-center text-white">
                        <i className="fas fa-chart-line"></i>
                      </div>
                      <div>
                        <p className="text-white font-medium">Progress Update</p>
                        <div className="w-32 h-1.5 bg-white/20 rounded-full mt-1">
                          <div className="h-full w-3/4 bg-white rounded-full"></div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Featured Courses - Dynamic Component */}
      <CourseList 
        title="Discover Learning Excellence"
        subtitle="Explore our comprehensive educational content spanning academic disciplines, technical skills, and professional development"
        limit={3} 
        featured={true}
      />

      {/* Blog & Resources - Dynamic Component */}
      <BlogPostList 
        title="Knowledge Resource Center"
        subtitle="Stay updated with industry trends, learning tips, and success stories to enhance your educational journey"
        limit={3}
      />

      {/* Testimonials - Dynamic Component */}
      <TestimonialList 
        title="What Our Learners Say"
        subtitle="Join our collaborative community where knowledge sharing and peer learning thrive"
        limit={3}
      />
      
      {/* Back to Top Button */}
      <button id="back-to-top" className="fixed bottom-8 right-8 w-12 h-12 bg-primary-600 hover:bg-primary-700 text-white rounded-full flex items-center justify-center shadow-lg z-50 transition-all opacity-0 invisible hover:scale-110 duration-300">
        <i className="fas fa-arrow-up"></i>
      </button>
    </MainLayout>
  );
};

export default HomePage;