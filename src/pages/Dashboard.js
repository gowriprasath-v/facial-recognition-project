import React, { useState } from 'react';
import { logout } from '../utils/auth';
import UploadProfile from '../components/UploadProfile';
import UploadGroup from '../components/UploadGroup';
import PhotoGallery from '../components/PhotoGallery';

const Dashboard = () => {
  const [activeTab, setActiveTab] = useState('profile');
  const [refreshGallery, setRefreshGallery] = useState(0);

  const handleUploadSuccess = () => {
    // Trigger gallery refresh
    setRefreshGallery(prev => prev + 1);
  };

  const handleLogout = () => {
    logout();
  };

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>🎯 Facial Recognition Dashboard</h1>
        <button onClick={handleLogout} className="logout-btn">
          Logout
        </button>
      </div>
      
      <div className="dashboard-nav">
        <button 
          className={activeTab === 'profile' ? 'active' : ''}
          onClick={() => setActiveTab('profile')}
        >
          Upload Profile
        </button>
        <button 
          className={activeTab === 'group' ? 'active' : ''}
          onClick={() => setActiveTab('group')}
        >
          Upload Group Photo
        </button>
        <button 
          className={activeTab === 'gallery' ? 'active' : ''}
          onClick={() => setActiveTab('gallery')}
        >
          My Photos
        </button>
      </div>
      
      <div className="dashboard-content">
        {activeTab === 'profile' && (
          <UploadProfile onUploadSuccess={handleUploadSuccess} />
        )}
        {activeTab === 'group' && (
          <UploadGroup onUploadSuccess={handleUploadSuccess} />
        )}
        {activeTab === 'gallery' && (
          <PhotoGallery key={refreshGallery} />
        )}
      </div>
    </div>
  );
};

export default Dashboard;
