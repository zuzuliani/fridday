from typing import Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
import os
from .memory import ChatbotMemory
from .session_manager import SessionManager
from .models import ChatRequest, ChatResponse, UserProfile
from .prompt_loader import get_chatbot_system_prompt
from utils.query_router import QueryRouter
from utils.react_reasoning import ReActReasoning

class ChatbotState:
    """State for the chatbot graph."""
    def __init__(self):
        self.user_input: str = ""
        self.ai_response: str = ""
        self.session_id: str = ""
        self.user_id: str = ""
        self.metadata: Dict[str, Any] = {}
        self.memory: Optional[ChatbotMemory] = None

class Chatbot:
    """Main chatbot class using LangGraph for conversation flow."""
    
    def __init__(self, supabase_client):
        self.supabase = supabase_client
        self.session_manager = SessionManager(supabase_client)
        
        # Initialize OpenAI
        self.llm = ChatOpenAI(
            model=os.getenv("DEFAULT_LLM", "gpt-3.5-turbo"),
            temperature=0.7,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Initialize routing components
        self.query_router = QueryRouter()
        self.react_reasoner = ReActReasoning()
        
        # Note: We'll create the prompt dynamically based on user profile
        # The base template structure will be the same, but system content will vary
        
        # Create LangGraph workflow
        self.workflow = self._create_workflow()
    
    def _get_personalized_system_prompt(self, user_profile: UserProfile = None) -> str:
        """Get system prompt personalized with user profile variables."""
        if not user_profile:
            # Use default prompt without variables
            print("🔍 No user profile provided, using defaults")
            return get_chatbot_system_prompt()
        
        # Convert user profile to dict for template variables
        variables = {
            "username": user_profile.username or "Usuário",
            "companyName": user_profile.companyName or "Sua empresa",
            "userRole": user_profile.userRole or "Profissional",
            "userFunction": user_profile.userFunction or "Cargo não especificado",
            "communication_tone": user_profile.communication_tone or "",
            "additional_guidelines": user_profile.additional_guidelines or ""
        }
        
        print(f"🔍 User profile variables: {variables}")
        result = get_chatbot_system_prompt(variables=variables)
        
        return result
    
    def _create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow for processing conversations."""
        
        def process_input(state: Dict[str, Any]) -> Dict[str, Any]:
            """Process user input and prepare for AI response."""
            memory = state["memory"]
            user_input = state["user_input"]
            
            # Add user message to memory
            conversation_id = memory.add_user_message(user_input, state.get("metadata", {}))
            state["conversation_id"] = conversation_id
            
            return state
        
        def route_query(state: Dict[str, Any]) -> Dict[str, Any]:
            """Route the query to appropriate processing path."""
            user_input = state["user_input"]
            memory = state["memory"]
            
            # Get conversation context for routing
            memory_vars = memory.get_memory_variables()
            history_text = ""
            if memory_vars.get("history"):
                # Convert last few messages to text for context
                recent_messages = memory_vars["history"][-3:]  # Last 3 messages
                history_text = " | ".join([msg.content[:50] for msg in recent_messages])
            
            # Determine routing
            route = self.query_router.route_query(user_input, history_text)
            route_explanation = self.query_router.get_routing_explanation(route, user_input)
            
            state["route"] = route
            state["route_explanation"] = route_explanation
            state["routing_info"] = {
                "route": route,
                "explanation": route_explanation,
                "user_input": user_input[:100] + "..." if len(user_input) > 100 else user_input
            }
            
            print(f"🔍 Query routed to: {route.upper()}")
            print(f"🔍 Route explanation: {route_explanation}")
            print(f"🔍 Routing info created: {state['routing_info']}")
            
            return state
        
        def generate_direct_response(state: Dict[str, Any]) -> Dict[str, Any]:
            """Generate direct AI response for simple queries."""
            memory = state["memory"]
            user_input = state["user_input"]
            user_profile = state.get("user_profile")
            
            print("🔍 Using DIRECT response path")
            
            # Get personalized system prompt
            system_prompt_content = self._get_personalized_system_prompt(user_profile)
            
            # Create prompt with personalized system message
            prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content=system_prompt_content),
                MessagesPlaceholder(variable_name="history"),
                HumanMessage(content="{input}")
            ])
            
            # Get memory variables
            memory_vars = memory.get_memory_variables()
            
            # Format prompt with history
            formatted_prompt = prompt.format_messages(
                history=memory_vars.get("history", []),
                input=user_input
            )
            
            # Generate response
            response = self.llm.invoke(formatted_prompt)
            ai_response = response.content
            
            # Add AI response to memory
            memory.add_ai_message(ai_response, state.get("metadata", {}))
            
            state["ai_response"] = ai_response
            state["reasoning_used"] = False
            
            # Include routing info in metadata
            metadata = state.get("metadata", {})
            if "routing_info" in state:
                metadata["routing_info"] = state["routing_info"]
            state["metadata"] = metadata
            
            return state
        
        async def generate_react_response(state: Dict[str, Any]) -> Dict[str, Any]:
            """Generate response using ReAct reasoning for complex queries."""
            memory = state["memory"]
            user_input = state["user_input"]
            user_profile = state.get("user_profile")

            print("🔍 Using REACT reasoning path")

            # Get personalized system prompt
            system_prompt_content = self._get_personalized_system_prompt(user_profile)

            # Get conversation history
            memory_vars = memory.get_memory_variables()
            conversation_history = memory_vars.get("history", [])

            # Create a placeholder conversation entry to get the ID for real-time updates
            conversation_id = memory.add_ai_message("Processing...", {})
            
            # Process with ReAct reasoning
            reasoning_result = await self.react_reasoner.process_with_reasoning(
                user_input=user_input,
                system_prompt=system_prompt_content,
                conversation_history=conversation_history,
                supabase_client=self.supabase,
                conversation_id=conversation_id
            )

            ai_response = reasoning_result["final_answer"]

            # Add reasoning metadata
            metadata = state.get("metadata", {})
            metadata.update({
                "step_count": reasoning_result["step_count"],
                "reasoning_used": True
            })

            # Update the placeholder conversation with final response and reflection steps
            try:
                self.supabase.table("conversations").update({
                    "content": ai_response,
                    "metadata": metadata,
                    "reflection_steps": reasoning_result["reasoning_steps"]
                }).eq("id", conversation_id).execute()
                print(f"🔍 Updated conversation {conversation_id} with final response")
            except Exception as e:
                print(f"Error updating final conversation: {e}")
                # Fallback to regular memory add if update fails
                memory.add_ai_message(ai_response, metadata, reflection_steps=reasoning_result["reasoning_steps"])

            state["ai_response"] = ai_response
            state["reasoning_used"] = True
            state["reasoning_steps"] = reasoning_result["reasoning_steps"]
            
            # Include routing info in metadata
            if "routing_info" in state:
                metadata["routing_info"] = state["routing_info"]
            
            return state
        
        # Create workflow graph
        workflow = StateGraph(dict)
        
        # Add nodes
        workflow.add_node("process_input", process_input)
        workflow.add_node("route_query", route_query)
        workflow.add_node("generate_direct_response", generate_direct_response)
        workflow.add_node("generate_react_response", generate_react_response)
        
        # Add edges
        workflow.add_edge("process_input", "route_query")
        
        # Conditional routing based on query complexity
        workflow.add_conditional_edges(
            "route_query",
            lambda state: state["route"],
            {
                "direct": "generate_direct_response",
                "react": "generate_react_response"
            }
        )
        
        workflow.add_edge("generate_direct_response", END)
        workflow.add_edge("generate_react_response", END)
        
        # Set entry point
        workflow.set_entry_point("process_input")
        
        return workflow.compile()
    
    async def chat(self, request: ChatRequest, user_id: str) -> ChatResponse:
        """Process a chat request and return response."""
        try:
            # Get or create session
            session = self.session_manager.get_session(request.session_id, user_id)
            if not session:
                session = self.session_manager.create_session(user_id)
            
            # Initialize memory for this session
            memory = ChatbotMemory(
                supabase_client=self.supabase,
                session_id=session.id,
                user_id=user_id
            )
            
            # Prepare state
            state = {
                "user_input": request.message,
                "session_id": session.id,
                "user_id": user_id,
                "metadata": request.metadata or {},
                "memory": memory,
                "conversation_id": "",
                "user_profile": request.user_profile
            }
            
            # Run workflow
            result = await self.workflow.ainvoke(state)
            
            # Update session timestamp
            self.session_manager.update_session(session.id, user_id)
            
            # Include routing information in metadata
            response_metadata = result.get("metadata", {})
            if "routing_info" in result:
                response_metadata["routing_info"] = result["routing_info"]
                print(f"🔍 Added routing_info to response: {result['routing_info']}")
            if "reasoning_steps" in result:
                response_metadata["reasoning_steps"] = result["reasoning_steps"]
                print(f"🔍 Added reasoning_steps to response: {len(result['reasoning_steps'])} steps")
            
            print(f"🔍 Final response metadata keys: {list(response_metadata.keys())}")
            
            return ChatResponse(
                message=result["ai_response"],
                session_id=session.id,
                conversation_id=result["conversation_id"],
                metadata=response_metadata
            )
            
        except Exception as e:
            print(f"Error in chat: {e}")
            raise
    
    def get_conversation_history(self, session_id: str, user_id: str) -> list:
        """Get conversation history for a session."""
        try:
            response = self.supabase.table("conversations").select("*").eq(
                "session_id", session_id
            ).eq("user_id", user_id).order("created_at", desc=False).execute()
            
            return response.data
        except Exception as e:
            print(f"Error getting conversation history: {e}")
            return []
    
    def create_new_session(self, user_id: str, title: str = None):
        """Create a new chat session."""
        return self.session_manager.create_session(user_id, title)
    
    def get_user_sessions(self, user_id: str):
        """Get all sessions for a user."""
        return self.session_manager.get_user_sessions(user_id)
    
    async def update_message(self, request, user_id: str):
        """Update an assistant message with LLM response - optimized version."""
        from .models import UpdateMessageResponse
        from datetime import datetime
        
        try:
            # 1. Get the message to update and verify ownership
            message_response = self.supabase.table("conversations").select("*").eq(
                "id", request.message_id
            ).eq("user_id", user_id).single().execute()
            
            if not message_response.data:
                raise Exception("Message not found or access denied")
            
            message = message_response.data
            session_id = message["session_id"]
            
            # 2. Update status to 'processing'
            self.supabase.table("conversations").update({
                "status": "processing"
            }).eq("id", request.message_id).execute()
            
            # 3. Get recent conversation context
            context_response = self.supabase.table("conversations").select("*").eq(
                "session_id", session_id
            ).eq("user_id", user_id).order("created_at", desc=False).limit(
                request.context_limit
            ).execute()
            
            context_messages = []
            for msg in context_response.data:
                if msg["id"] != request.message_id:  # Don't include the empty assistant message
                    context_messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
            
            # 4. Get LLM response
            try:
                # Convert to LangChain format
                from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
                
                lc_messages = []
                for msg in context_messages:
                    if msg["role"] == "user":
                        lc_messages.append(HumanMessage(content=msg["content"]))
                    elif msg["role"] == "assistant":
                        lc_messages.append(AIMessage(content=msg["content"]))
                    elif msg["role"] == "system":
                        lc_messages.append(SystemMessage(content=msg["content"]))
                
                # Get response from LLM
                response = await self.llm.ainvoke(lc_messages)
                assistant_content = response.content
                
            except Exception as llm_error:
                # Mark as failed and re-raise
                self.supabase.table("conversations").update({
                    "status": "failed",
                    "content": f"Error: {str(llm_error)}"
                }).eq("id", request.message_id).execute()
                raise llm_error
            
            # 5. Update the assistant message with LLM response
            update_response = self.supabase.table("conversations").update({
                "content": assistant_content,
                "status": "complete"
            }).eq("id", request.message_id).execute()
            
            updated_message = update_response.data[0]
            
            return UpdateMessageResponse(
                message_id=updated_message["id"],
                content=updated_message["content"],
                status=updated_message["status"],
                session_id=updated_message["session_id"],
                updated_at=datetime.fromisoformat(updated_message["updated_at"].replace('Z', '+00:00'))
            )
            
        except Exception as e:
            # Try to mark as failed if we have the message_id
            try:
                self.supabase.table("conversations").update({
                    "status": "failed"
                }).eq("id", request.message_id).execute()
            except:
                pass  # Ignore errors when trying to update status
            
            print(f"Error in update_message: {e}")
            raise

    async def update_message_with_profile(self, request, user_id: str):
        """Update an assistant message with personalized LLM response - for WeWeb organic chat flow."""
        from .models import UpdateMessageResponse
        from datetime import datetime
        
        try:
            # 1. Get the message to update and verify ownership
            message_response = self.supabase.table("conversations").select("*").eq(
                "id", request.message_id
            ).eq("user_id", user_id).single().execute()
            
            if not message_response.data:
                raise Exception("Message not found or access denied")
            
            message = message_response.data
            session_id = message["session_id"]
            
            # 2. Update status to 'processing'
            self.supabase.table("conversations").update({
                "status": "processing"
            }).eq("id", request.message_id).execute()
            
            # 3. Get recent conversation context (excluding the empty assistant message)
            context_response = self.supabase.table("conversations").select("*").eq(
                "session_id", session_id
            ).eq("user_id", user_id).order("created_at", desc=False).limit(
                request.context_limit * 2  # Get more to account for filtering
            ).execute()
            
            context_messages = []
            for msg in context_response.data:
                if msg["id"] != request.message_id:  # Don't include the empty assistant message
                    context_messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
            
            # Take only the last context_limit messages after filtering
            context_messages = context_messages[-request.context_limit:]
            
            # 4. Determine if we should use ReAct reasoning based on the last user message
            last_user_message = ""
            for msg in reversed(context_messages):
                if msg["role"] == "user":
                    last_user_message = msg["content"]
                    break
            
            # Route the query to determine processing approach
            route = "direct"
            if last_user_message:
                # Simple routing logic - you can enhance this
                complex_keywords = ["pesquisar", "buscar", "comparar", "analisar", "research", "search", "compare", "analyze"]
                if any(keyword in last_user_message.lower() for keyword in complex_keywords):
                    route = "react"
            
            print(f"🔍 Processing with route: {route.upper()}")
            
            # 5. Get personalized system prompt
            system_prompt_content = self._get_personalized_system_prompt(request.user_profile)
            
            # 6. Generate response based on route
            if route == "react":
                # Use ReAct reasoning for complex queries
                assistant_content = await self._generate_react_response_for_update(
                    context_messages, system_prompt_content, request.message_id
                )
            else:
                # Use direct response for simple queries
                assistant_content = await self._generate_direct_response_for_update(
                    context_messages, system_prompt_content
                )
            
            # 7. Update the assistant message with final response
            update_response = self.supabase.table("conversations").update({
                "content": assistant_content,
                "status": "complete"
            }).eq("id", request.message_id).execute()
            
            updated_message = update_response.data[0]
            
            return UpdateMessageResponse(
                message_id=updated_message["id"],
                content=updated_message["content"],
                status=updated_message["status"],
                session_id=updated_message["session_id"],
                updated_at=datetime.fromisoformat(updated_message["updated_at"].replace('Z', '+00:00'))
            )
            
        except Exception as e:
            # Try to mark as failed if we have the message_id
            try:
                self.supabase.table("conversations").update({
                    "status": "failed",
                    "content": f"Error: {str(e)}"
                }).eq("id", request.message_id).execute()
            except:
                pass  # Ignore errors when trying to update status
            
            print(f"Error in update_message_with_profile: {e}")
            raise
    
    async def _generate_direct_response_for_update(self, context_messages, system_prompt_content):
        """Generate direct LLM response for update flow."""
        from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
        
        # Convert context to LangChain format
        lc_messages = [SystemMessage(content=system_prompt_content)]
        
        for msg in context_messages:
            if msg["role"] == "user":
                lc_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                lc_messages.append(AIMessage(content=msg["content"]))
        
        # Get response from LLM
        response = await self.llm.ainvoke(lc_messages)
        return response.content
    
    async def _generate_react_response_for_update(self, context_messages, system_prompt_content, conversation_id):
        """Generate ReAct reasoning response for update flow."""
        # Get the last user message for ReAct processing
        last_user_message = ""
        for msg in reversed(context_messages):
            if msg["role"] == "user":
                last_user_message = msg["content"]
                break
        
        if not last_user_message:
            # Fallback to direct response if no user message found
            return await self._generate_direct_response_for_update(context_messages, system_prompt_content)
        
        # Convert context to LangChain message format for history
        from langchain_core.messages import HumanMessage, AIMessage
        conversation_history = []
        
        for msg in context_messages[:-1]:  # Exclude the last user message as it will be processed separately
            if msg["role"] == "user":
                conversation_history.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                conversation_history.append(AIMessage(content=msg["content"]))
        
        # Process with ReAct reasoning
        reasoning_result = await self.react_reasoner.process_with_reasoning(
            user_input=last_user_message,
            system_prompt=system_prompt_content,
            conversation_history=conversation_history,
            supabase_client=self.supabase,
            conversation_id=conversation_id
        )
        
        return reasoning_result["final_answer"]
    
    async def start_message_processing(self, request, user_id: str):
        """Start processing an assistant message in the background - returns immediately."""
        from .models import ProcessingStartedResponse
        import asyncio
        
        try:
            # 1. Verify message exists and belongs to user
            message_response = self.supabase.table("conversations").select("*").eq(
                "id", request.message_id
            ).eq("user_id", user_id).single().execute()
            
            if not message_response.data:
                raise Exception("Message not found or access denied")
            
            message = message_response.data
            session_id = message["session_id"]
            
            # 2. Immediately set status to "processing"
            self.supabase.table("conversations").update({
                "status": "processing"
            }).eq("id", request.message_id).execute()
            
            # 3. Start background task (fire and forget)
            asyncio.create_task(self._process_message_background(request, user_id))
            
            # 4. Return immediately with processing status
            return ProcessingStartedResponse(
                message_id=request.message_id,
                status="processing",
                session_id=session_id,
                message="Message processing started - watch database for completion"
            )
            
        except Exception as e:
            # Try to mark as failed if we have the message_id
            try:
                self.supabase.table("conversations").update({
                    "status": "failed",
                    "content": f"Error: {str(e)}"
                }).eq("id", request.message_id).execute()
            except:
                pass
            
            print(f"Error in start_message_processing: {e}")
            raise
    
    async def _process_message_background(self, request, user_id: str):
        """Background task to process the message - this runs asynchronously."""
        try:
            print(f"🔄 Starting background processing for message {request.message_id}")
            
            # Get message info
            message_response = self.supabase.table("conversations").select("*").eq(
                "id", request.message_id
            ).eq("user_id", user_id).single().execute()
            
            if not message_response.data:
                raise Exception("Message not found during background processing")
            
            message = message_response.data
            session_id = message["session_id"]
            
            # Get conversation context (excluding the empty assistant message)
            context_response = self.supabase.table("conversations").select("*").eq(
                "session_id", session_id
            ).eq("user_id", user_id).order("created_at", desc=False).limit(
                request.context_limit * 2  # Get more to account for filtering
            ).execute()
            
            context_messages = []
            for msg in context_response.data:
                if msg["id"] != request.message_id:  # Don't include the empty assistant message
                    context_messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
            
            # Take only the last context_limit messages after filtering
            context_messages = context_messages[-request.context_limit:]
            
            # Determine routing based on the last user message
            last_user_message = ""
            for msg in reversed(context_messages):
                if msg["role"] == "user":
                    last_user_message = msg["content"]
                    break
            
            # Route the query
            route = "direct"
            if last_user_message:
                complex_keywords = ["pesquisar", "buscar", "comparar", "analisar", "research", "search", "compare", "analyze"]
                if any(keyword in last_user_message.lower() for keyword in complex_keywords):
                    route = "react"
            
            print(f"🔍 Background processing with route: {route.upper()}")
            
            # Get personalized system prompt
            system_prompt_content = self._get_personalized_system_prompt(request.user_profile)
            
            # Generate response based on route
            if route == "react":
                assistant_content = await self._generate_react_response_for_update(
                    context_messages, system_prompt_content, request.message_id
                )
            else:
                assistant_content = await self._generate_direct_response_for_update(
                    context_messages, system_prompt_content
                )
            
            # Update the assistant message with final response
            self.supabase.table("conversations").update({
                "content": assistant_content,
                "status": "complete"
            }).eq("id", request.message_id).execute()
            
            print(f"✅ Background processing completed for message {request.message_id}")
            
        except Exception as e:
            print(f"❌ Background processing failed for message {request.message_id}: {e}")
            
            # Mark as failed
            try:
                self.supabase.table("conversations").update({
                    "status": "failed",
                    "content": f"Processing failed: {str(e)}"
                }).eq("id", request.message_id).execute()
            except:
                pass