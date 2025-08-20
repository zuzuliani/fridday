# auth_utils/supAuth.py
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_EMAIL = os.getenv("SUPABASE_EMAIL")
SUPABASE_PASSWORD = os.getenv("SUPABASE_PASSWORD")

class SupAuth:
    def __init__(self, token=None):
        self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        if token:
            self.supabase.postgrest.auth(token)
        else:
            # login local
            response = self.supabase.auth.sign_in_with_password({
                "email": SUPABASE_EMAIL,
                "password": SUPABASE_PASSWORD
            })
            self.session = response.session
            self.token = self.session.access_token
            self.supabase.postgrest.auth(self.token)

    def add(self, table, data):
        return self.supabase.table(table).insert(data).execute()

    def select(self, table, columns="*", filters=None):
        q = self.supabase.table(table).select(columns)
        if filters:
            for key, value in filters.items():
                q = q.eq(key, value)
        return q.execute()

    def update(self, table, id, data):
        return self.supabase.table(table).update(data).eq('id', id).execute()

    def get_token(self):
        return self.token
