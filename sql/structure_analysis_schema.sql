-- Create structureAnalysis table
CREATE TABLE IF NOT EXISTS structureAnalysis (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    prompt TEXT,
    reportStructure TEXT,
    information JSONB[] DEFAULT '{}',
    visibility TEXT NOT NULL DEFAULT 'private' CHECK (visibility IN ('public', 'private')),
    owner UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_structureAnalysis_updated_at ON structureAnalysis;
CREATE TRIGGER update_structureAnalysis_updated_at
    BEFORE UPDATE ON structureAnalysis
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create roles and users_roles tables first (needed for is_admin function)
-- Optional: Create roles table if it doesn't exist
CREATE TABLE IF NOT EXISTS roles (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name TEXT NOT NULL UNIQUE CHECK (name IN ('admin', 'user', 'moderator')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Optional: Create users_roles table if it doesn't exist
-- (This assumes you have a user roles system)
CREATE TABLE IF NOT EXISTS users_roles (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, role_id)
);

-- Create a security definer function to check admin role without recursion
-- This must be created before any RLS policies that reference it
CREATE OR REPLACE FUNCTION is_admin(user_id UUID DEFAULT auth.uid())
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    -- Direct query without RLS to avoid recursion
    RETURN EXISTS (
        SELECT 1 FROM users_roles ur
        JOIN roles r ON ur.role_id = r.id
        WHERE ur.user_id = COALESCE(user_id, auth.uid()) 
        AND r.name = 'admin'
    );
END;
$$;

-- Enable RLS
ALTER TABLE structureAnalysis ENABLE ROW LEVEL SECURITY;

-- Create RLS Policies

-- Policy 1: Users can view public records and their own records
DROP POLICY IF EXISTS "Users can view public and own structureAnalysis" ON structureAnalysis;
CREATE POLICY "Users can view public and own structureAnalysis" ON structureAnalysis
    FOR SELECT
    USING (
        visibility = 'public' 
        OR owner = auth.uid()
        OR is_admin()
    );

-- Policy 2: Users can insert their own records
DROP POLICY IF EXISTS "Users can insert own structureAnalysis" ON structureAnalysis;
CREATE POLICY "Users can insert own structureAnalysis" ON structureAnalysis
    FOR INSERT
    WITH CHECK (
        owner = auth.uid()
        OR is_admin()
    );

-- Policy 3: Users can update their own records or admins can update all
DROP POLICY IF EXISTS "Users can update own structureAnalysis" ON structureAnalysis;
CREATE POLICY "Users can update own structureAnalysis" ON structureAnalysis
    FOR UPDATE
    USING (
        owner = auth.uid()
        OR is_admin()
    )
    WITH CHECK (
        owner = auth.uid()
        OR is_admin()
    );

-- Policy 4: Users can delete their own records or admins can delete all
DROP POLICY IF EXISTS "Users can delete own structureAnalysis" ON structureAnalysis;
CREATE POLICY "Users can delete own structureAnalysis" ON structureAnalysis
    FOR DELETE
    USING (
        owner = auth.uid()
        OR is_admin()
    );

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_structureAnalysis_owner ON structureAnalysis(owner);
CREATE INDEX IF NOT EXISTS idx_structureAnalysis_visibility ON structureAnalysis(visibility);
CREATE INDEX IF NOT EXISTS idx_structureAnalysis_created_at ON structureAnalysis(created_at DESC);





-- Enable RLS on users_roles
ALTER TABLE users_roles ENABLE ROW LEVEL SECURITY;

-- RLS Policy for users_roles: Users can only see their own roles, admins can see all
DROP POLICY IF EXISTS "Users can view own roles, admins can view all" ON users_roles;
CREATE POLICY "Users can view own roles, admins can view all" ON users_roles
    FOR SELECT
    USING (
        user_id = auth.uid()
        OR is_admin()
    );

-- Create indexes on roles
CREATE INDEX IF NOT EXISTS idx_roles_name ON roles(name);

-- Create indexes on users_roles
CREATE INDEX IF NOT EXISTS idx_users_roles_user_id ON users_roles(user_id);
CREATE INDEX IF NOT EXISTS idx_users_roles_role_id ON users_roles(role_id);

-- Insert default roles
INSERT INTO roles (name) VALUES 
    ('admin'),
    ('user'),
    ('moderator')
ON CONFLICT (name) DO NOTHING;