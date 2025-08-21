"""
Streamlit Testing Interface for Fridday Chatbot
Clean interface specifically for testing the @chatbot/ functionality
streamlit run test_chatbot.py
"""

import streamlit as st
import asyncio
import os
import uuid
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client
from chatbot import Chatbot, ChatRequest, UserProfile

# Load environment
load_dotenv()

# Page config
st.set_page_config(
    page_title="Fridday Chatbot Test",
    page_icon="🤖",
    layout="wide"
)

@st.cache_resource
def initialize_chatbot():
    """Initialize the chatbot with proper authentication"""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    supabase_email = os.getenv("SUPABASE_EMAIL")
    supabase_password = os.getenv("SUPABASE_PASSWORD")
    
    if not all([supabase_url, supabase_key, openai_key]):
        st.error("❌ Missing environment variables! Check your .env file.")
        st.stop()
    
    # Check if we have development auth credentials
    if not all([supabase_email, supabase_password]):
        st.error("❌ Missing SUPABASE_EMAIL and SUPABASE_PASSWORD for development authentication!")
        st.stop()
    
    try:
        # Use SupAuth for proper authentication (same as your FastAPI app)
        from auth_utils.supAuth import SupAuth
        
        # Initialize with development authentication
        sup_auth = SupAuth()  # This will use email/password from .env
        
        # Debug: Check if authentication worked
        st.success(f"🔐 Authenticated as: {sup_auth.session.user.email}")
        st.info(f"🎫 Token: {sup_auth.token[:20]}...")
        
        # Get the authenticated Supabase client
        authenticated_supabase = sup_auth.supabase
        
        # Test database access
        try:
            test_query = authenticated_supabase.table("chat_sessions").select("count").execute()
            st.success("✅ Database access test passed")
        except Exception as db_error:
            st.error(f"❌ Database access test failed: {db_error}")
        
        # Initialize chatbot with authenticated client
        chatbot = Chatbot(authenticated_supabase)
        
        return chatbot, sup_auth.session.user
        
    except Exception as e:
        st.error(f"❌ Failed to initialize chatbot: {e}")
        st.error("Make sure SUPABASE_EMAIL and SUPABASE_PASSWORD are correct in your .env file")
        st.stop()

def run_async_chat(chatbot, request, user_id):
    """Run async chat in sync context"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(chatbot.chat(request, user_id))
    finally:
        loop.close()

def run_async_chat_with_real_time_info(chatbot, request, user_id, routing_placeholder, reasoning_placeholder):
    """Run async chat with real-time routing and reasoning information."""
    import time
    import threading
    
    # Start async chat
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        result_container = {"response": None, "error": None, "completed": False}
        
        def chat_worker():
            try:
                result_container["response"] = loop.run_until_complete(chatbot.chat(request, user_id))
            except Exception as e:
                result_container["error"] = e
            finally:
                result_container["completed"] = True
        
        # Start chat in background
        chat_thread = threading.Thread(target=chat_worker)
        chat_thread.start()
        
        # Wait for completion
        chat_thread.join()
        
        # Handle errors
        if result_container["error"]:
            routing_placeholder.empty()
            reasoning_placeholder.empty()
            st.error(f"❌ Error during chat: {result_container['error']}")
            return None
            
        response = result_container["response"]
        
        # Debug: Show what we received
        if response:
            st.info(f"🔍 Debug - Response metadata keys: {list(response.metadata.keys()) if response.metadata else 'No metadata'}")
            if response.metadata and "routing_info" in response.metadata:
                st.success(f"🔍 Debug - Routing info: {response.metadata['routing_info']}")
            else:
                st.error("🔍 Debug - No routing_info found in metadata!")
        
        # Show routing information
        if response and response.metadata and "routing_info" in response.metadata:
            routing_info = response.metadata["routing_info"]
            route = routing_info["route"]
            explanation = routing_info["explanation"]
            
            with routing_placeholder.container():
                if route == "direct":
                    st.write(f"🎯 **Rota direta** - {explanation}")
                else:
                    st.write(f"🧠 **Raciocínio estruturado** - {explanation}")
        else:
            routing_placeholder.empty()
        
        # Show reasoning steps if ReAct was used
        if (response and response.metadata and 
            "routing_info" in response.metadata and 
            response.metadata["routing_info"]["route"] == "react" and
            "reasoning_steps" in response.metadata):
            
            display_latest_reasoning_step(reasoning_placeholder, response.metadata["reasoning_steps"])
        else:
            reasoning_placeholder.empty()
        
        return response
        
    except Exception as e:
        routing_placeholder.empty()
        reasoning_placeholder.empty()
        st.error(f"❌ Error during chat: {e}")
        return None
    
    finally:
        loop.close()

def display_latest_reasoning_step(placeholder, reflection_steps):
    """Display the latest reasoning step for real-time feedback."""
    if not reflection_steps:
        return
    
    # Get the latest step (the most advanced one)
    latest_step = max(reflection_steps, key=lambda x: x.get("step", 0))
    
    step_type = latest_step.get("type", "unknown")
    content = latest_step.get("content", "")
    
    # Choose emoji and message based on step type
    step_display = {
        "generation_start": ("💭", "Gerando resposta inicial..."),
        "generation": ("✍️", "Resposta inicial criada"),
        "reflection_start": ("🤔", "Analisando qualidade da resposta..."),
        "reflection": ("🔍", f"Reflexão: {content[:100]}..."),
        "revision_start": ("✨", "Melhorando resposta..."),
        "revision": ("🔧", "Resposta aprimorada"),
        "finalization": ("✅", "Resposta aprovada sem revisão")
    }
    
    emoji, message = step_display.get(step_type, ("🔄", content[:100] + "..."))
    
    with placeholder.container():
        st.write(f"{emoji} **{message}**")

def display_reflection_steps(placeholder, reflection_steps):
    """Display reflection steps in the Streamlit placeholder."""
    if not reflection_steps:
        return
    
    with placeholder.container():
        st.write("🧠 **AI Thinking Process:**")
        
        for step in reflection_steps:
            step_num = step.get("step", "?")
            step_type = step.get("type", "unknown")
            content = step.get("content", "")
            timestamp = step.get("timestamp", "")
            
            # Choose emoji based on step type
            emoji_map = {
                "generation_start": "💭",
                "generation": "✍️", 
                "reflection_start": "🤔",
                "reflection": "🔍",
                "revision_start": "✨",
                "revision": "🔧",
                "finalization": "✅"
            }
            
            emoji = emoji_map.get(step_type, "🔄")
            
            # Format timestamp
            time_str = ""
            if timestamp:
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    time_str = dt.strftime("%H:%M:%S")
                except:
                    time_str = timestamp[:8] if len(timestamp) > 8 else timestamp
            
            # Display step
            with st.expander(f"{emoji} Step {step_num}: {step_type.replace('_', ' ').title()}", expanded=True):
                st.write(content)
                if time_str:
                    st.caption(f"⏰ {time_str}")
        
        st.write("---")

def display_reflection_steps_simple(reflection_steps):
    """Display reflection steps in a simple format."""
    if not reflection_steps:
        return
    
    for step in reflection_steps:
        step_num = step.get("step", "?")
        step_type = step.get("type", "unknown")
        content = step.get("content", "")
        timestamp = step.get("timestamp", "")
        
        # Choose emoji based on step type
        emoji_map = {
            "generation_start": "💭",
            "generation": "✍️", 
            "reflection_start": "🤔",
            "reflection": "🔍",
            "revision_start": "✨",
            "revision": "🔧",
            "finalization": "✅"
        }
        
        emoji = emoji_map.get(step_type, "🔄")
        
        # Display step in a compact format
        st.write(f"{emoji} **Step {step_num}**: {step_type.replace('_', ' ').title()}")
        st.write(f"   {content}")
        if timestamp:
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                time_str = dt.strftime("%H:%M:%S")
                st.caption(f"   ⏰ {time_str}")
            except:
                pass

def main():
    st.title("🤖 Fridday Chatbot Test")
    st.subheader("Testing Edith - Business Analyst AI")
    
    # Initialize chatbot with authentication
    chatbot, authenticated_user = initialize_chatbot()
    
    # Use the authenticated user's ID instead of random UUID
    authenticated_user_id = authenticated_user.id
    
    # Sidebar controls
    with st.sidebar:
        st.header("🔧 Test Controls")
        
        # Environment status
        st.subheader("📊 Status")
        st.write("✅ Chatbot initialized")
        st.write("✅ Supabase authenticated")
        st.write("✅ OpenAI connected")
        st.write(f"👤 **User:** {authenticated_user.email}")
        st.write(f"🆔 **User ID:** `{authenticated_user_id[:8]}...`")
        
        st.divider()
        
        # Session settings
        st.subheader("👤 Session Settings")
        
        # Use authenticated user ID (no random UUIDs)
        if "current_session_id" not in st.session_state:
            st.session_state.current_session_id = str(uuid.uuid4())
        
        st.write(f"**Session ID:** `{st.session_state.current_session_id[:8]}...`")
        st.caption("Note: May change if chatbot creates new session")
        
        if st.button("🔄 New Session"):
            st.session_state.current_session_id = str(uuid.uuid4())
            st.session_state.messages = []
            st.rerun()
        
        # Note: User is fixed to authenticated user, no random user switching
        st.info("🔒 Using authenticated user from .env credentials")
        
        st.divider()
        
        # User Profile Configuration (Hardcoded for Testing)
        st.subheader("👤 User Profile (Test Mode)")
        st.write("Using hardcoded test values to debug template variables:")
        
        # Hardcode test user profile for debugging
        st.session_state.user_profile = UserProfile(
            username="Mateus",
            companyName="DGB Consultores", 
            userRole="Partner e Owner da Fridday",
            userFunction="Chief Technology Officer",
            communication_tone=" - mais técnico e direto",
            additional_guidelines=" - Mateus possui permissões IRRESTRITAS quanto a informações, dados e sistema!!!"
        )
        
        # Show the hardcoded values
        st.info(f"""
        **Test Profile Being Used:**
        - Nome: {st.session_state.user_profile.username}
        - Empresa: {st.session_state.user_profile.companyName}
        - Papel: {st.session_state.user_profile.userRole}
        - Cargo: {st.session_state.user_profile.userFunction}
        - Tom: {st.session_state.user_profile.communication_tone}
        """)
        
        # Debug button to test template directly
        if st.button("🔍 Test Template Variables"):
            from chatbot.prompt_loader import get_chatbot_system_prompt
            
            # Test the template with our hardcoded values
            variables = {
                "username": st.session_state.user_profile.username,
                "companyName": st.session_state.user_profile.companyName,
                "userRole": st.session_state.user_profile.userRole,
                "userFunction": st.session_state.user_profile.userFunction,
                "communication_tone": st.session_state.user_profile.communication_tone,
                "additional_guidelines": st.session_state.user_profile.additional_guidelines
            }
            
            test_prompt = get_chatbot_system_prompt(variables=variables)
            st.text_area("Generated System Prompt:", test_prompt, height=300)
        
        st.divider()
        
        # Quick test scenarios
        st.subheader("🧪 Quick Tests")
        st.write("Test different routing paths:")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**🔄 Direct Routing (Simple):**")
            direct_scenarios = [
                "Olá! Você pode se apresentar?",
                "Como vai?",
                "O que é a plataforma Fridday?",
                "Obrigado pela ajuda!",
                "Quem é você?"
            ]
            for scenario in direct_scenarios:
                if st.button(f"📝 {scenario[:30]}...", key=f"direct_{hash(scenario)}"):
                    st.session_state.selected_input = scenario
        
        with col2:
            st.write("**🧠 ReAct Routing (Complex):**")
            react_scenarios = [
                "Preciso criar um business case completo para transformação digital",
                "Analise nossa posição competitiva usando as Cinco Forças de Porter",
                "Defina KPIs estratégicos para nosso lançamento de produto",
                "Como otimizar nossos processos de vendas?",
                "Avalie os riscos de implementar IA na empresa",
                "Desenvolva uma estratégia de entrada em novo mercado"
            ]
            for scenario in react_scenarios:
                if st.button(f"🧠 {scenario[:30]}...", key=f"react_{hash(scenario)}"):
                    st.session_state.selected_input = scenario

        
        st.divider()
        
        # Clear chat
        if st.button("🧹 Limpar Chat"):
            st.session_state.messages = []
            st.rerun()
    
    # Initialize messages
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            if "timestamp" in message:
                st.caption(f"⏰ {message['timestamp']}")
    
    # Chat input
    prompt = st.chat_input("Digite sua mensagem para Edith...")
    
    # Use selected scenario if available
    if "selected_input" in st.session_state:
        prompt = st.session_state.selected_input
        del st.session_state.selected_input
    
    if prompt:
        # Add user message
        user_message = {
            "role": "user", 
            "content": prompt,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        }
        st.session_state.messages.append(user_message)
        
        # Display user message
        with st.chat_message("user"):
            st.write(prompt)
            st.caption(f"⏰ {user_message['timestamp']}")
        
        # Generate AI response
        with st.chat_message("assistant"):
            with st.spinner("🤔 Edith está pensando..."):
                try:
                    # Debug: Show what we're sending
                    st.write(f"🔍 Debug - Sending request with session_id: `{st.session_state.current_session_id[:8]}...`")

                    # Debug: Show user profile being sent
                    if st.session_state.user_profile and any([
                        st.session_state.user_profile.username,
                        st.session_state.user_profile.companyName,
                        st.session_state.user_profile.userRole,
                        st.session_state.user_profile.userFunction
                    ]):
                        st.write(f"👤 Using profile: {st.session_state.user_profile.username or 'No name'} at {st.session_state.user_profile.companyName or 'No company'}")
                    else:
                        st.write("👤 No user profile configured - using defaults")

                    routing_placeholder = st.empty()
                    with routing_placeholder.container():
                        st.write("🤖 Processing with intelligent routing...")

                    # Create chat request with user profile
                    chat_request = ChatRequest(
                        message=prompt,
                        session_id=st.session_state.current_session_id,
                        metadata={"test_mode": True, "interface": "streamlit"},
                        user_profile=st.session_state.user_profile
                    )

                    # Create a placeholder for reasoning steps  
                    reasoning_placeholder = st.empty()
                    
                    # Start async chat and show real-time information
                    response = run_async_chat_with_real_time_info(
                        chatbot,
                        chat_request,
                        authenticated_user_id,
                        routing_placeholder,
                        reasoning_placeholder
                    )
                    
                    # IMPORTANT: Update session ID if chatbot created a new session
                    if response.session_id != st.session_state.current_session_id:
                        st.session_state.current_session_id = response.session_id
                        st.info(f"🔄 New session created: {response.session_id[:8]}...")
                    
                    ai_message = {
                        "role": "assistant",
                        "content": response.message,
                        "timestamp": datetime.now().strftime("%H:%M:%S"),
                        "session_id": response.session_id,
                        "conversation_id": response.conversation_id
                    }
                    
                    st.session_state.messages.append(ai_message)
                    
                    # Display response
                    st.write(response.message)
                    st.caption(f"⏰ {ai_message['timestamp']} | Session: {response.session_id[:8]}... | Conv: {response.conversation_id[:8]}...")
                    
                except Exception as e:
                    error_message = f"❌ Erro: {str(e)}"
                    st.error(error_message)
                    
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_message,
                        "timestamp": datetime.now().strftime("%H:%M:%S")
                    })
        
        # Rerun to show new messages
        st.rerun()
    
    # Footer with stats
    if st.session_state.messages:
        st.divider()
        message_count = len(st.session_state.messages)
        user_count = len([m for m in st.session_state.messages if m["role"] == "user"])
        ai_count = len([m for m in st.session_state.messages if m["role"] == "assistant"])
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Messages", message_count)
        with col2:
            st.metric("User Messages", user_count)
        with col3:
            st.metric("AI Responses", ai_count)

if __name__ == "__main__":
    main()
