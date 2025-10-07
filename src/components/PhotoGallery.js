import React, { useState, useEffect } from 'react';
import { photosAPI } from '../services/api';

const PhotoGallery = () => {
  const [photos, setPhotos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadPhotos();
  }, []);

  const loadPhotos = async () => {
    try {
      const response = await photosAPI.getMyPhotos();
      
      if (response.data.status === 'success') {
        setPhotos(response.data.data.photos || []);
      }
    } catch (err) {
      setError('Failed to load photos');
    }
    
    setLoading(false);
  };

  if (loading) {
    return <div className="loading">Loading your photos...</div>;
  }

  if (error) {
    return <div className="error-message">{error}</div>;
  }

  if (photos.length === 0) {
    return (
      <div className="no-photos">
        <h3>No Photos Found</h3>
        <p>Upload a profile photo and group photos to see matches here!</p>
      </div>
    );
  }

  return (
    <div className="photo-gallery">
      <h3>Your Matched Photos ({photos.length})</h3>
      <div className="photo-grid">
        {photos.map((photo, index) => (
          <div key={index} className="photo-item">
            <img 
              src={`http://localhost:5000/uploads/groups/${photo.filename}`} 
              alt={`Group photo ${index + 1}`}
            />
            <div className="photo-info">
              <p>Uploaded: {new Date(photo.uploaded_at).toLocaleDateString()}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default PhotoGallery;
