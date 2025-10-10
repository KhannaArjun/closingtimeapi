# Admin Login API Guide

This document explains how to use the admin login API for your closingtime admin app.

## Available Endpoints

### 1. Admin Login
**Endpoint:** `POST /admin/login`

**Description:** Authenticates admin user with simple credentials

**Request Body:**
```json
{
    "username": "admin",
    "password": "admin"
}
```

**Success Response:**
```json
{
    "message": "Success",
    "error": false,
    "data": {
        "username": "admin",
        "role": "admin",
        "session_token": "a1b2c3d4e5f6...",
        "login_time": "2024-01-01T12:00:00.000Z"
    }
}
```

**Error Response:**
```json
{
    "message": "Invalid credentials",
    "error": true,
    "data": {}
}
```

### 2. Admin Health Check
**Endpoint:** `GET /admin/health`

**Description:** Simple health check for admin API (no authentication required)

**Success Response:**
```json
{
    "message": "Admin API is running",
    "error": false,
    "data": {
        "status": "healthy",
        "timestamp": "2024-01-01T12:00:00.000Z"
    }
}
```

### 3. Protected Admin Test Endpoint
**Endpoint:** `GET /admin/test`

**Description:** Test endpoint to verify admin authentication

**Headers Required:**
```
Authorization: Bearer <session_token>
```

**Success Response:**
```json
{
    "message": "Admin access granted",
    "error": false,
    "data": {
        "message": "This is a protected admin endpoint",
        "timestamp": "2024-01-01T12:00:00.000Z"
    }
}
```

## Usage in Your Admin App

### 1. Login Flow
```javascript
// Example in JavaScript/Node.js
const loginAdmin = async () => {
    try {
        const response = await fetch('https://closingtimeapi.onrender.com/admin/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                username: 'admin',
                password: 'admin'
            })
        });
        
        const result = await response.json();
        
        if (!result.error) {
            // Store the session token
            localStorage.setItem('admin_token', result.data.session_token);
            console.log('Admin login successful!');
            return result.data.session_token;
        } else {
            console.error('Login failed:', result.message);
            return null;
        }
    } catch (error) {
        console.error('Login error:', error);
        return null;
    }
};
```

### 2. Using Protected Endpoints
```javascript
// Example of calling a protected endpoint
const callProtectedEndpoint = async (endpoint) => {
    const token = localStorage.getItem('admin_token');
    
    if (!token) {
        console.error('No admin token found');
        return null;
    }
    
    try {
        const response = await fetch(endpoint, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
            }
        });
        
        const result = await response.json();
        
        if (!result.error) {
            return result.data;
        } else {
            console.error('API call failed:', result.message);
            return null;
        }
    } catch (error) {
        console.error('API error:', error);
        return null;
    }
};
```

### 3. Python Example
```python
import requests

# Login
def admin_login():
    url = "https://closingtimeapi.onrender.com/admin/login"
    data = {
        "username": "admin",
        "password": "admin"
    }
    
    response = requests.post(url, json=data)
    result = response.json()
    
    if not result.get('error'):
        return result['data']['session_token']
    else:
        print(f"Login failed: {result.get('message')}")
        return None

# Use token for protected endpoints
def call_protected_endpoint(token, endpoint):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(endpoint, headers=headers)
    return response.json()
```

## Authentication Decorator

If you need to create additional admin-only endpoints, you can use the `@require_admin_token` decorator:

```python
@app.route('/admin/your-endpoint', methods=['GET'])
@require_admin_token
def your_admin_endpoint():
    # Your admin-only logic here
    return flask.jsonify(api_response.apiResponse("Success", False, your_data))
```

## Security Notes

- This is a simple implementation for internal use
- The admin credentials are hardcoded (admin/admin)
- Session tokens are generated but not stored/validated against a database
- For production use, consider implementing proper JWT tokens or database-stored sessions
- Consider adding rate limiting to prevent brute force attacks

## Testing

Run the test script to verify the API is working:

```bash
python admin_login_test.py
```

Make sure to update the `BASE_URL` in the test script to match your server URL.

## Production URLs

- **Local Development:** `http://localhost:5000`
- **Production:** `https://closingtimeapi.onrender.com`
