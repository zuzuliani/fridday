-- Add reflection_steps column to conversations table
-- This stores the reflection steps as an array of JSONB objects
-- for frontend display of the AI's thinking process

ALTER TABLE conversations 
ADD COLUMN reflection_steps JSONB[] DEFAULT NULL;

-- Add a comment to document the column
COMMENT ON COLUMN conversations.reflection_steps IS 'Array of JSONB objects containing reflection steps for complex queries. Structure: [{"step": 1, "type": "generation|reflection|revision|finalization", "content": "...", "timestamp": "ISO datetime"}]';

-- Create an index for querying reflection steps if needed
CREATE INDEX idx_conversations_reflection_steps 
ON conversations USING GIN (reflection_steps);

-- Example query to find conversations that used reasoning:
-- SELECT * FROM conversations WHERE reflection_steps IS NOT NULL AND array_length(reflection_steps, 1) > 0;

-- Example query to count reflection steps:
-- SELECT id, content, array_length(reflection_steps, 1) as step_count FROM conversations WHERE reflection_steps IS NOT NULL;
