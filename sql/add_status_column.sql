-- Add status column to conversations table for tracking message completion
ALTER TABLE conversations 
ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'pending' 
CHECK (status IN ('pending', 'processing', 'complete', 'failed'));

-- Create index for efficient status queries
CREATE INDEX IF NOT EXISTS idx_conversations_status 
    ON conversations(status, updated_at);

-- Update existing messages to 'complete' status
UPDATE conversations 
SET status = 'complete' 
WHERE status IS NULL;