# Admin API Guide

This document explains how to use the admin API for your closingtime admin app. The admin system uses database-backed authentication with session management.

## Available Endpoints

### 1. Admin Registration
**Endpoint:** `POST /admin/register`

**Description:** Register a new admin user (Note: You may want to protect or disable this endpoint after initial setup)

**Request Body:**
```json
{
    "name": "Admin Name",
    "email": "admin@example.com",
    "password": "yourpassword"
}
```

**Success Response:**
```json
{
    "message": "Admin registered successfully",
    "error": false,
    "data": {
        "user_id": "507f1f77bcf86cd799439011",
        "name": "Admin Name",
        "email": "admin@example.com",
        "role": "Admin"
    }
}
```

**Error Response:**
```json
{
    "message": "Admin with this email already exists",
    "error": true,
    "data": {}
}
```

### 2. Admin Login
**Endpoint:** `POST /admin/login`

**Description:** Authenticates admin user against database and returns session token

**Request Body:**
```json
{
    "email": "admin@example.com",
    "password": "yourpassword"
}
```

**Success Response:**
```json
{
    "message": "Success",
    "error": false,
    "data": {
        "user_id": "507f1f77bcf86cd799439011",
        "name": "Admin Name",
        "email": "admin@example.com",
        "role": "Admin",
        "session_token": "a1b2c3d4e5f6789abcdef...",
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

### 3. Admin Logout
**Endpoint:** `POST /admin/logout`

**Description:** Logout admin user and invalidate session token

**Headers Required:**
```
Authorization: Bearer <session_token>
```

**Success Response:**
```json
{
    "message": "Logged out successfully",
    "error": false,
    "data": {}
}
```

**Error Response:**
```json
{
    "message": "Session not found",
    "error": true,
    "data": {}
}
```

### 4. Admin Health Check
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

### 5. Protected Admin Test Endpoint
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

### 1. First Time Setup - Register Admin
```javascript
// Register first admin user (do this once)
const registerAdmin = async () => {
    try {
        const response = await fetch('https://closingtimeapi.onrender.com/admin/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                name: 'Admin User',
                email: 'admin@closingtime.com',
                password: 'your_secure_password'
            })
        });
        
        const result = await response.json();
        
        if (!result.error) {
            console.log('Admin registered successfully!', result.data);
            return result.data;
        } else {
            console.error('Registration failed:', result.message);
            return null;
        }
    } catch (error) {
        console.error('Registration error:', error);
        return null;
    }
};
```

### 2. Login Flow
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
                email: 'admin@closingtime.com',
                password: 'your_secure_password'
            })
        });
        
        const result = await response.json();
        
        if (!result.error) {
            // Store the session token (valid for 24 hours)
            localStorage.setItem('admin_token', result.data.session_token);
            localStorage.setItem('admin_user', JSON.stringify(result.data));
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

### 3. Logout Flow
```javascript
// Logout admin user
const logoutAdmin = async () => {
    const token = localStorage.getItem('admin_token');
    
    if (!token) {
        console.log('No active session');
        return;
    }
    
    try {
        const response = await fetch('https://closingtimeapi.onrender.com/admin/logout', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
            }
        });
        
        const result = await response.json();
        
        // Clear local storage regardless of response
        localStorage.removeItem('admin_token');
        localStorage.removeItem('admin_user');
        
        if (!result.error) {
            console.log('Logged out successfully');
        }
    } catch (error) {
        console.error('Logout error:', error);
        // Clear local storage even on error
        localStorage.removeItem('admin_token');
        localStorage.removeItem('admin_user');
    }
};
```

### 4. Using Protected Endpoints
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

### 5. Python Example
```python
import requests

# Register admin (first time only)
def register_admin():
    url = "https://closingtimeapi.onrender.com/admin/register"
    data = {
        "name": "Admin User",
        "email": "admin@closingtime.com",
        "password": "your_secure_password"
    }
    
    response = requests.post(url, json=data)
    result = response.json()
    
    if not result.get('error'):
        print(f"Admin registered: {result['data']}")
        return result['data']
    else:
        print(f"Registration failed: {result.get('message')}")
        return None

# Login
def admin_login():
    url = "https://closingtimeapi.onrender.com/admin/login"
    data = {
        "email": "admin@closingtime.com",
        "password": "your_secure_password"
    }
    
    response = requests.post(url, json=data)
    result = response.json()
    
    if not result.get('error'):
        return result['data']['session_token']
    else:
        print(f"Login failed: {result.get('message')}")
        return None

# Logout
def admin_logout(token):
    url = "https://closingtimeapi.onrender.com/admin/logout"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, headers=headers)
    return response.json()

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

### Database Collections Used
- **`admin_registration`** - Stores admin user accounts with encrypted passwords
- **`admin_sessions`** - Stores active session tokens with expiration times

### Security Features
- ✅ **Database-backed authentication** - Admin credentials stored in MongoDB
- ✅ **Password encryption** - Passwords stored using base64 encoding (same as donor system)
- ✅ **Session management** - Tokens stored in database with 24-hour expiration
- ✅ **Token validation** - Each request validates token against database
- ✅ **Automatic expiration** - Expired sessions are automatically cleaned up
- ✅ **Logout support** - Sessions can be explicitly invalidated

### Recommendations
- 🔒 Consider protecting `/admin/register` endpoint after initial setup
- 🔐 Use strong passwords for admin accounts
- ⏱️ Session tokens expire after 24 hours
- 🚫 Consider adding rate limiting to prevent brute force attacks
- 🔑 For higher security, consider upgrading from base64 to bcrypt password hashing

## Testing

Run the test script to verify the API is working:

```bash
python admin_login_test.py
```

Make sure to update the `BASE_URL` in the test script to match your server URL.

## Production URLs

- **Local Development:** `http://localhost:5000`
- **Production:** `https://closingtimeapi.onrender.com`
