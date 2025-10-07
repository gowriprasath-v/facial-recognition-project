import pytest
import json
from app import create_app

@pytest.fixture
def app():
    app = create_app('testing')
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_health_endpoint(client):
    """Test health check endpoint"""
    response = client.get('/api/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'status' in data

def test_register_user(client):
    """Test user registration"""
    user_data = {
        'username': 'testuser',
        'password': 'testpass123',
        'email': 'test@example.com'
    }
    response = client.post('/api/auth/register', 
                          json=user_data,
                          content_type='application/json')
    
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['status'] == 'success'
    assert 'access_token' in data['data']

def test_login_user(client):
    """Test user login"""
    # First register
    user_data = {
        'username': 'testuser2',
        'password': 'testpass123'
    }
    client.post('/api/auth/register', json=user_data)
    
    # Then login
    login_data = {
        'username': 'testuser2',
        'password': 'testpass123'
    }
    response = client.post('/api/auth/login', 
                          json=login_data,
                          content_type='application/json')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success'
    assert 'access_token' in data['data']
