import React, { useState } from 'react';
import { uploadAPI } from '../services/api';

const UploadGroup = ({ onUploadSuccess }) => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleFileSelect = (e) => {
    const file = e.target.files;
    if (file) {
      setSelectedFile(file);
      
      // Create preview
      const reader = new FileReader();
      reader.onloadend = () => {
        setPreview(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setError('Please select a file first');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const response = await uploadAPI.uploadGroup(selectedFile);
      
      if (response.data.status === 'success') {
        setSuccess('Group photo uploaded successfully!');
        if (onUploadSuccess) onUploadSuccess();
      }
    } catch (err) {
      setError(err.response?.data?.message || 'Upload failed');
    }
    
    setLoading(false);
  };

  return (
    <div className="upload-section">
      <h3>Upload Group Photo</h3>
      <div className="file-upload">
        <input
          type="file"
          accept="image/*"
          onChange={handleFileSelect}
          id="group-upload"
        />
        <label htmlFor="group-upload" className="file-upload-label">
          Choose Group Photo
        </label>
        
        {preview && (
          <div className="image-preview">
            <img src={preview} alt="Preview" />
          </div>
        )}
        
        {selectedFile && (
          <p className="file-info">
            Selected: {selectedFile.name}
          </p>
        )}
        
        {error && <div className="error-message">{error}</div>}
        {success && <div className="success-message">{success}</div>}
        
        <button 
          onClick={handleUpload} 
          disabled={loading || !selectedFile}
          className="upload-btn"
        >
          {loading ? 'Uploading...' : 'Upload Group Photo'}
        </button>
      </div>
    </div>
  );
};

export default UploadGroup;
