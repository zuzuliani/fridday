# fridday-edith-ai Chatbot

A sophisticated chatbot built with LangChain, LangGraph, and Supabase, featuring session management and persistent memory.

## Features

- 🤖 **LangChain & LangGraph**: Advanced conversation flows and AI capabilities
- 💾 **Persistent Memory**: Conversation history stored in Supabase with intelligent summarization
- 🔐 **Authentication**: JWT-based auth with Supabase (local dev mode available)
- 📱 **Session Management**: Create and manage multiple conversation sessions
- 🛡️ **Row Level Security**: Secure data access with Supabase RLS policies
- 🚀 **FastAPI**: High-performance API with automatic documentation
- ☁️ **Railway Ready**: Configured for easy deployment to Railway
- ⚙️ **Configurable LLM**: Use any OpenAI model via `DEFAULT_LLM` environment variable

## Quick Start

### 1. Environment Setup

Copy the example environment file and configure it:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# Environment
VERSION=development  # or production

# Supabase Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_EMAIL=your_email@example.com
SUPABASE_PASSWORD=your_password

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key
DEFAULT_LLM=gpt-3.5-turbo

# Tavily Configuration (for research tools)
TAVILY_API_KEY=your_tavily_api_key

# Application Configuration
APP_HOST=0.0.0.0
APP_PORT=8000
```

### 2. Database Setup

Run the SQL schema in your Supabase dashboard:

```bash
# Execute the contents of sql/conversations_schema.sql in your Supabase SQL editor
```

This will create:
- `conversations` table with RLS policies
- `chat_sessions` table with RLS policies
- Proper indexes for performance

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Application

```bash
python main.py
```

The API will be available at:
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **Health**: http://localhost:8000/api/v1/health

## API Endpoints

### Authentication

All endpoints require authentication via JWT token in the `Authorization` header:

```
Authorization: Bearer <your-jwt-token>
```

In development mode (`VERSION=development`), the local Supabase auth is used automatically.

### Chat Endpoints

#### POST `/api/v1/chat`
Send a message to the chatbot.

**Request:**
```json
{
  "message": "Hello, how are you?",
  "session_id": "session-uuid",
  "metadata": {},
  "user_profile": {
    "username": "João Silva",
    "companyName": "TechCorp",
    "userRole": "Gerente de Projetos", 
    "userFunction": "Diretor de TI",
    "communication_tone": " - mais executivo",
    "additional_guidelines": " - foque em ROI e métricas"
  }
}
```

**Note:** The `user_profile` field is optional. If not provided, the chatbot uses default prompt without personalization.

**Response:**
```json
{
  "message": "Hello! I'm doing great, thank you for asking. How can I help you today?",
  "session_id": "session-uuid",
  "conversation_id": "conversation-uuid",
  "metadata": {}
}
```

#### POST `/api/v1/sessions`
Create a new chat session.

**Request:**
```json
{
  "title": "My Chat Session"  // optional
}
```

#### GET `/api/v1/sessions`
Get all sessions for the current user.

#### GET `/api/v1/sessions/{session_id}/history`
Get conversation history for a specific session.

#### DELETE `/api/v1/sessions/{session_id}`
Delete a chat session and all its conversations.

## Architecture

### Memory Management

The chatbot uses a sophisticated memory system:

1. **LangChain ConversationSummaryBufferMemory**: Automatically summarizes old conversations when they exceed token limits
2. **Supabase Persistence**: All conversations are stored permanently in the database
3. **Session-based Organization**: Conversations are organized into sessions for better context management

### Authentication Flow

- **Development**: Uses local Supabase authentication from `supabase_auth/` module
- **Production**: Validates JWT tokens from the `Authorization` header
- **Row Level Security**: Ensures users can only access their own data

### LangGraph Workflow

The chatbot uses LangGraph to manage conversation flow:

1. **Process Input**: Validates and stores user message
2. **Generate Response**: Uses LangChain with conversation history to generate AI response
3. **Update Memory**: Stores AI response and updates conversation summary if needed

## Deployment

### Railway Deployment

1. **Connect Repository**: Connect your GitHub repository to Railway
2. **Set Environment Variables**: Configure these in Railway dashboard:
   ```env
   VERSION=production
   SUPABASE_URL=your_production_supabase_url
   SUPABASE_KEY=your_production_supabase_key
   OPENAI_API_KEY=your_openai_api_key
   DEFAULT_LLM=gpt-4
   TAVILY_API_KEY=your_tavily_api_key
   APP_HOST=0.0.0.0
   APP_PORT=8000
   ```
3. **Deploy**: Railway will automatically deploy using the `main.py` file
4. **Access**: Your API will be available at `https://your-app.railway.app`

### API Access After Deployment

Once deployed, your chatbot API will be publicly accessible:

- **Base URL**: `https://your-app.railway.app`
- **API Docs**: `https://your-app.railway.app/docs`
- **Health Check**: `https://your-app.railway.app/api/v1/health`

#### Example API Usage:
```bash
# Send a message to the chatbot
curl -X POST "https://your-app.railway.app/api/v1/chat" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!", "session_id": "your-session-id"}'
```

See `examples/api_examples.md` for comprehensive API usage examples.

### Environment Variables for Production

```env
VERSION=production
SUPABASE_URL=your_production_supabase_url
SUPABASE_KEY=your_production_supabase_key
OPENAI_API_KEY=your_openai_api_key
DEFAULT_LLM=gpt-4
TAVILY_API_KEY=your_tavily_api_key
APP_HOST=0.0.0.0
APP_PORT=8000
```

## Development

### Project Structure

```
fridday-edith-ai/
├── supabase_auth/          # Local authentication utilities
├── chatbot/                # Core chatbot logic
│   ├── models.py          # Pydantic models
│   ├── memory.py          # Memory management
│   ├── session_manager.py # Session handling
│   └── chatbot.py         # Main chatbot class
├── api/                   # FastAPI routes and auth
│   ├── auth.py           # Authentication logic
│   └── routes.py         # API endpoints
├── sql/                  # Database schema
├── main.py              # FastAPI application
└── requirements.txt     # Dependencies
```

### Adding New Features

1. **Extend the LangGraph workflow** in `chatbot/chatbot.py`
2. **Add new API endpoints** in `api/routes.py`
3. **Create new models** in `chatbot/models.py`
4. **Update database schema** in `sql/conversations_schema.sql`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

MIT License - see LICENSE file for details