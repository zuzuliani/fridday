-- Create conversations table for chatbot
CREATE TABLE IF NOT EXISTS conversations (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    session_id VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for efficient querying
CREATE INDEX IF NOT EXISTS idx_conversations_user_session 
    ON conversations(user_id, session_id, created_at);

-- Create index for session-based queries
CREATE INDEX IF NOT EXISTS idx_conversations_session 
    ON conversations(session_id, created_at);

-- Enable Row Level Security
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
-- Users can only see their own conversations
CREATE POLICY "Users can view their own conversations" 
    ON conversations 
    FOR SELECT 
    USING (auth.uid() = user_id);

-- Users can only insert their own conversations
CREATE POLICY "Users can insert their own conversations" 
    ON conversations 
    FOR INSERT 
    WITH CHECK (auth.uid() = user_id);

-- Users can only update their own conversations
CREATE POLICY "Users can update their own conversations" 
    ON conversations 
    FOR UPDATE 
    USING (auth.uid() = user_id);

-- Users can only delete their own conversations
CREATE POLICY "Users can delete their own conversations" 
    ON conversations 
    FOR DELETE 
    USING (auth.uid() = user_id);

-- Create a function to update the updated_at column
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at
CREATE TRIGGER update_conversations_updated_at 
    BEFORE UPDATE ON conversations 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Create sessions table for session management
CREATE TABLE IF NOT EXISTS chat_sessions (
    id VARCHAR(255) PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    title VARCHAR(255),
    summary TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

-- Enable RLS for sessions
ALTER TABLE chat_sessions ENABLE ROW LEVEL SECURITY;

-- RLS policies for sessions
CREATE POLICY "Users can view their own sessions" 
    ON chat_sessions 
    FOR SELECT 
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own sessions" 
    ON chat_sessions 
    FOR INSERT 
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own sessions" 
    ON chat_sessions 
    FOR UPDATE 
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own sessions" 
    ON chat_sessions 
    FOR DELETE 
    USING (auth.uid() = user_id);

-- Trigger for sessions
CREATE TRIGGER update_sessions_updated_at 
    BEFORE UPDATE ON chat_sessions 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();