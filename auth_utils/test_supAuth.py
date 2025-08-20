from .supAuth import SupAuth

sup = SupAuth()  # login local
token = sup.get_token()
"""
res = sup.select("conversations")
for row in res.data:
    print(row["content"])
"""

# Get user ID from the session
user_id = sup.session.user.id

# Add a new conversation with required fields
sup.add("conversations", {
    "role": "user",
    "content": "Olá!",
    "session_id": "test_session_1",
    "user_id": user_id
})
