import React from 'react';
import Header from './Header';
import Footer from './Footer';

const MainLayout = ({ children }) => {
  return (
    <div className="flex flex-col min-h-screen w-full">
        
      <Header />
      <main className="flex-grow w-full overflow-x-hidden">
        {children}
      </main>
      <Footer />
    </div>
  );
};

export default MainLayout;