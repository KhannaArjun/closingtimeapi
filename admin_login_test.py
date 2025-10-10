#!/usr/bin/env python3
"""
Test script for the admin login API
Run this to test if your admin login endpoints are working correctly
"""

import requests
import json

# Change this to your server URL
BASE_URL = "http://localhost:5000"  # For local testing
# BASE_URL = "https://closingtimeapi.onrender.com"  # For production

def test_admin_login():
    """Test the admin login endpoint"""
    print("🔐 Testing Admin Login...")
    
    login_data = {
        "username": "admin",
        "password": "admin"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/admin/login", json=login_data)
        result = response.json()
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if not result.get('error') and result.get('data', {}).get('session_token'):
            print("✅ Admin login successful!")
            return result['data']['session_token']
        else:
            print("❌ Admin login failed!")
            return None
            
    except Exception as e:
        print(f"❌ Error during login: {str(e)}")
        return None

def test_admin_health():
    """Test the admin health endpoint"""
    print("\n🏥 Testing Admin Health...")
    
    try:
        response = requests.get(f"{BASE_URL}/admin/health")
        result = response.json()
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(result, indent=2)}")
        
    except Exception as e:
        print(f"❌ Error during health check: {str(e)}")

if __name__ == "__main__":
    print("🚀 Testing Admin Login API...\n")
    
    # Update BASE_URL to match your server before running
    print(f"Testing against: {BASE_URL}")
    print("(Update BASE_URL in this script if needed)\n")
    
    test_admin_health()
    test_admin_login()
    
    print("\n✨ Test completed!")
