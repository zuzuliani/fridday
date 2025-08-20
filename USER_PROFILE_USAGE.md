# User Profile Variables - Strategic Implementation

## 🎯 **Overview**

Your system prompt now supports dynamic personalization using template variables. This works seamlessly across both the test interface and production API.

## 📝 **Template Variables in `system_prompt.md`**

```markdown
Nome do usuário: {username}
Empresa do usuário: {companyName}
Papel do usuário: {userRole}
Cargo do usuário: {userFunction}

- **Profissional, porém acessível**{communication_tone}
- **Sempre considere o impacto comercial e o ROI** das recomendações{additional_guidelines}
```

## 🚀 **Usage Examples**

### **1. Test Interface (Streamlit)**

```bash
streamlit run test_chatbot.py
```

- Fill out the **User Profile** form in the sidebar
- Save profile and start chatting
- Edith will use your personalized information

### **2. API Usage (Production)**

```python
from chatbot import ChatRequest, UserProfile

# Create user profile
user_profile = UserProfile(
    username="João Silva",
    companyName="TechCorp",
    userRole="Gerente de Projetos",
    userFunction="Diretor de TI",
    communication_tone=" - mais executivo",
    additional_guidelines=" - sempre inclua métricas e KPIs"
)

# Create chat request with profile
request = ChatRequest(
    message="Preciso de ajuda com transformação digital",
    session_id="session-uuid",
    user_profile=user_profile
)

# Send to chatbot
response = await chatbot.chat(request, user_id)
```

### **3. WeWeb Integration**

When you receive JWT from WeWeb, you can extract user profile data and pass it:

```python
# In your API endpoint
@app.post("/api/v1/chat")
async def chat_endpoint(
    request: ChatRequest,
    user = Depends(get_current_user)
):
    # If user profile not provided, you could extract from JWT/database
    if not request.user_profile:
        request.user_profile = UserProfile(
            username=user.get("name"),
            companyName=user.get("company"),
            userRole=user.get("role"),
            userFunction=user.get("function")
        )
    
    response = await chatbot.chat(request, user["id"])
    return response
```

## 🔧 **How It Works**

1. **Template Variables**: `{username}`, `{companyName}`, etc. in `system_prompt.md`
2. **UserProfile Model**: Structured data for user information
3. **Dynamic Prompt Generation**: `_get_personalized_system_prompt()` method
4. **Fallback Handling**: Default values if profile not provided

## ✨ **Benefits**

- ✅ **Personalized Responses**: Edith addresses users by name and company
- ✅ **Context-Aware**: Responses tailored to user role and function  
- ✅ **Flexible Tone**: Adjustable communication style
- ✅ **Business Focus**: Custom guidelines for specific needs
- ✅ **Backward Compatible**: Works without profile (uses defaults)

## 🎯 **Example Transformation**

**Before:**
> "Hello! I'm Edith, your Business Analyst AI assistant..."

**After (with profile):**
> "Olá João Silva! Sou Edith, sua assistente de Business Analyst AI dentro da TechCorp. Como Diretor de TI, posso ajudá-lo com estratégias executivas focadas em ROI e métricas..."

## 📋 **Next Steps**

1. **Test with Streamlit** - Try different profile configurations
2. **Update API routes** - Pass user profile data from WeWeb JWT
3. **Enhance system prompt** - Add more personalization variables as needed

Your prompt system is now ready for production with full personalization! 🚀
