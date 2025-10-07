from app import create_app
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Create app
app = create_app('development')

if __name__ == '__main__':
    print("🚀 Starting Facial Recognition Backend...")
    print("📊 Server running at: http://localhost:5000")
    print("🔍 API endpoints available:")
    print("   - POST /api/auth/register")
    print("   - POST /api/auth/login") 
    print("   - POST /api/upload/profile")
    print("   - POST /api/upload/group")
    print("   - GET  /api/upload/my-photos")
    print("   - GET  /api/upload/test-ml")
    
    app.run(debug=True, port=5000, use_reloader=False)
