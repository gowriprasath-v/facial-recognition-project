import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Login from '../components/Login';
import Register from '../components/Register';

const HomePage = () => {
  const [showLogin, setShowLogin] = useState(true);
  const navigate = useNavigate();

  const handleAuthSuccess = () => {
    navigate('/dashboard');
  };

  return (
    <div className="home-page">
      <div className="header">
        <h1>🎯 Image Sorting with Facial Recognition</h1>
        <p>Find yourself in group photos automatically!</p>
      </div>
      
      <div className="auth-container">
        {showLogin ? (
          <Login 
            onSuccess={handleAuthSuccess}
            switchToRegister={() => setShowLogin(false)}
          />
        ) : (
          <Register 
            onSuccess={handleAuthSuccess}
            switchToLogin={() => setShowLogin(true)}
          />
        )}
      </div>
    </div>
  );
};

export default HomePage;
