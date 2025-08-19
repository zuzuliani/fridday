-- Create my_structured_analysis table
CREATE TABLE IF NOT EXISTS my_structured_analysis (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name TEXT NOT NULL,
    company_name TEXT,
    company_industry TEXT,
    company_description TEXT,
    report TEXT,
    questions JSONB[] DEFAULT '{}',
    owner_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    structured_analysis_id UUID NOT NULL REFERENCES structureAnalysis(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create updated_at trigger (reuse existing function)
DROP TRIGGER IF EXISTS update_my_structured_analysis_updated_at ON my_structured_analysis;
CREATE TRIGGER update_my_structured_analysis_updated_at
    BEFORE UPDATE ON my_structured_analysis
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Enable RLS
ALTER TABLE my_structured_analysis ENABLE ROW LEVEL SECURITY;

-- Create RLS Policies

-- Policy 1: Users can view their own records, admins can view all
DROP POLICY IF EXISTS "Users can view own my_structured_analysis" ON my_structured_analysis;
CREATE POLICY "Users can view own my_structured_analysis" ON my_structured_analysis
    FOR SELECT
    USING (
        owner_id = auth.uid()
        OR is_admin()
    );

-- Policy 2: Users can insert their own records, admins can insert all
DROP POLICY IF EXISTS "Users can insert own my_structured_analysis" ON my_structured_analysis;
CREATE POLICY "Users can insert own my_structured_analysis" ON my_structured_analysis
    FOR INSERT
    WITH CHECK (
        owner_id = auth.uid()
        OR is_admin()
    );

-- Policy 3: Users can update their own records, admins can update all
DROP POLICY IF EXISTS "Users can update own my_structured_analysis" ON my_structured_analysis;
CREATE POLICY "Users can update own my_structured_analysis" ON my_structured_analysis
    FOR UPDATE
    USING (
        owner_id = auth.uid()
        OR is_admin()
    )
    WITH CHECK (
        owner_id = auth.uid()
        OR is_admin()
    );

-- Policy 4: Users can delete their own records, admins can delete all
DROP POLICY IF EXISTS "Users can delete own my_structured_analysis" ON my_structured_analysis;
CREATE POLICY "Users can delete own my_structured_analysis" ON my_structured_analysis
    FOR DELETE
    USING (
        owner_id = auth.uid()
        OR is_admin()
    );

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_my_structured_analysis_owner_id ON my_structured_analysis(owner_id);
CREATE INDEX IF NOT EXISTS idx_my_structured_analysis_structured_analysis_id ON my_structured_analysis(structured_analysis_id);
CREATE INDEX IF NOT EXISTS idx_my_structured_analysis_created_at ON my_structured_analysis(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_my_structured_analysis_company_name ON my_structured_analysis(company_name);
CREATE INDEX IF NOT EXISTS idx_my_structured_analysis_company_industry ON my_structured_analysis(company_industry);
