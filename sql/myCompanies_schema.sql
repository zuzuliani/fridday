-- Create myCompanies table
CREATE TABLE IF NOT EXISTS myCompanies (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name TEXT NOT NULL,
    industry TEXT,
    description TEXT,
    owner UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create updated_at trigger (reuse existing function)
DROP TRIGGER IF EXISTS update_myCompanies_updated_at ON myCompanies;
CREATE TRIGGER update_myCompanies_updated_at
    BEFORE UPDATE ON myCompanies
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Enable RLS
ALTER TABLE myCompanies ENABLE ROW LEVEL SECURITY;

-- Create RLS Policies

-- Policy 1: Users can view their own records, admins can view all
DROP POLICY IF EXISTS "Users can view own myCompanies" ON myCompanies;
CREATE POLICY "Users can view own myCompanies" ON myCompanies
    FOR SELECT
    USING (
        owner = auth.uid()
        OR is_admin()
    );

-- Policy 2: Users can insert their own records, admins can insert all
DROP POLICY IF EXISTS "Users can insert own myCompanies" ON myCompanies;
CREATE POLICY "Users can insert own myCompanies" ON myCompanies
    FOR INSERT
    WITH CHECK (
        owner = auth.uid()
        OR is_admin()
    );

-- Policy 3: Users can update their own records, admins can update all
DROP POLICY IF EXISTS "Users can update own myCompanies" ON myCompanies;
CREATE POLICY "Users can update own myCompanies" ON myCompanies
    FOR UPDATE
    USING (
        owner = auth.uid()
        OR is_admin()
    )
    WITH CHECK (
        owner = auth.uid()
        OR is_admin()
    );

-- Policy 4: Users can delete their own records, admins can delete all
DROP POLICY IF EXISTS "Users can delete own myCompanies" ON myCompanies;
CREATE POLICY "Users can delete own myCompanies" ON myCompanies
    FOR DELETE
    USING (
        owner = auth.uid()
        OR is_admin()
    );

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_myCompanies_owner ON myCompanies(owner);
CREATE INDEX IF NOT EXISTS idx_myCompanies_name ON myCompanies(name);
CREATE INDEX IF NOT EXISTS idx_myCompanies_industry ON myCompanies(industry);
CREATE INDEX IF NOT EXISTS idx_myCompanies_created_at ON myCompanies(created_at DESC);
