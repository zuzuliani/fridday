# BifrostAI Chatbot API Examples

These examples show how to interact with the deployed chatbot API using various tools.

## Base URL
Replace `https://your-app.railway.app` with your actual Railway deployment URL.

## Authentication
All requests require a JWT token in the Authorization header:
```
Authorization: Bearer YOUR_JWT_TOKEN
```

## cURL Examples

### 1. Health Check
```bash
curl -X GET "https://your-app.railway.app/api/v1/health"
```

### 2. Create a New Session
```bash
curl -X POST "https://your-app.railway.app/api/v1/sessions" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "My Chat Session"}'
```

### 3. Send a Message to Chatbot
```bash
curl -X POST "https://your-app.railway.app/api/v1/chat" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, how can you help me?",
    "session_id": "YOUR_SESSION_ID",
    "metadata": {}
  }'
```

### 4. Get All Sessions
```bash
curl -X GET "https://your-app.railway.app/api/v1/sessions" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 5. Get Conversation History
```bash
curl -X GET "https://your-app.railway.app/api/v1/sessions/YOUR_SESSION_ID/history" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 6. Delete a Session
```bash
curl -X DELETE "https://your-app.railway.app/api/v1/sessions/YOUR_SESSION_ID" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## JavaScript/Fetch Examples

### Send a Message
```javascript
const response = await fetch('https://your-app.railway.app/api/v1/chat', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer YOUR_JWT_TOKEN',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    message: "What's the weather like?",
    session_id: "your-session-id"
  })
});

const data = await response.json();
console.log('Bot response:', data.message);
```

### Create Session and Start Conversation
```javascript
// Create a session
const sessionResponse = await fetch('https://your-app.railway.app/api/v1/sessions', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer YOUR_JWT_TOKEN',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    title: "JavaScript Chat"
  })
});

const session = await sessionResponse.json();
const sessionId = session.id;

// Send a message
const chatResponse = await fetch('https://your-app.railway.app/api/v1/chat', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer YOUR_JWT_TOKEN',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    message: "Hello from JavaScript!",
    session_id: sessionId
  })
});

const chatData = await chatResponse.json();
console.log('Bot:', chatData.message);
```

## Python Requests Examples

### Simple Chat Example
```python
import requests

API_BASE = "https://your-app.railway.app"
JWT_TOKEN = "your_jwt_token"

headers = {
    "Authorization": f"Bearer {JWT_TOKEN}",
    "Content-Type": "application/json"
}

# Create session
session_response = requests.post(
    f"{API_BASE}/api/v1/sessions",
    json={"title": "Python Chat"},
    headers=headers
)
session_id = session_response.json()["id"]

# Send message
chat_response = requests.post(
    f"{API_BASE}/api/v1/chat",
    json={
        "message": "Hello from Python!",
        "session_id": session_id
    },
    headers=headers
)

print("Bot response:", chat_response.json()["message"])
```

## Getting JWT Tokens

### Frontend (Supabase Auth)
```javascript
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY)

// Sign in
const { data, error } = await supabase.auth.signInWithPassword({
  email: 'user@example.com',
  password: 'password'
})

if (data.session) {
  const jwtToken = data.session.access_token
  // Use this token for API calls
}
```

### Backend (Service Key)
For server-to-server communication, you can use Supabase service keys, but be careful with permissions.

## Response Formats

### Chat Response
```json
{
  "message": "Hello! How can I help you today?",
  "session_id": "9bd064e4-744c-4c6d-adf1-4b57f0040738",
  "conversation_id": "9e8ffc2f-cc3a-4aba-a1e5-3db82abafd94",
  "metadata": {}
}
```

### Session Response
```json
{
  "id": "9bd064e4-744c-4c6d-adf1-4b57f0040738",
  "user_id": "aa2751d0-68b1-4656-8965-0ee54ae6f39d",
  "title": "My Chat Session",
  "summary": null,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "is_active": true
}
```

### Conversation History Response
```json
{
  "session_id": "9bd064e4-744c-4c6d-adf1-4b57f0040738",
  "messages": [
    {
      "id": "msg-1",
      "role": "user",
      "content": "Hello!",
      "created_at": "2024-01-15T10:30:00Z"
    },
    {
      "id": "msg-2", 
      "role": "assistant",
      "content": "Hello! How can I help you?",
      "created_at": "2024-01-15T10:30:01Z"
    }
  ]
}
```

## Error Handling

### Authentication Error (401)
```json
{
  "detail": "Authentication failed: Invalid token"
}
```

### Session Not Found (404)
```json
{
  "detail": "Session not found"
}
```

### Server Error (500)
```json
{
  "detail": "Chat error: Connection timeout"
}
```