#!/usr/bin/env python3
import os
from app import create_app

def main():
    config_name = os.getenv('FLASK_ENV', 'development')
    app = create_app(config_name)
    
    print("=" * 50)
    print("🚀 Facial Recognition Backend")
    print("=" * 50)
    print(f"Environment: {config_name}")
    print("Server: http://localhost:5000")
    print("Health: http://localhost:5000/api/health")
    print("Endpoints:")
    print("- POST /api/auth/register")
    print("- POST /api/auth/login")  
    print("- GET  /api/auth/profile")
    print("- POST /api/upload/profile")
    print("- POST /api/upload/group")
    print("- GET  /api/photos/my-photos")
    print("=" * 50)
    
    app.run(
        debug=True if config_name == 'development' else False,
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5000))
    )

if __name__ == '__main__':
    main()
