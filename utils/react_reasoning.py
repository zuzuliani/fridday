"""
Reflection Pattern Implementation for Fridday Chatbot
A general-purpose thinking machine with tool capability foundation

This module implements a reflection pattern where the AI:
1. Generates an initial response
2. Reflects on that response critically  
3. Revises if improvements are identified

Future enhancement: Tool integration can be added to the generate/revise steps
for external data retrieval, calculations, or other tool-based operations.
"""

from typing import Dict, Any, List, TypedDict, Optional
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage, AIMessage
from langgraph.graph import StateGraph, END
from datetime import datetime
import os

class ReflectionState(TypedDict):
    """State for reflection workflow"""
    user_input: str
    system_prompt: str
    conversation_history: List
    draft_response: str
    reflection: str
    final_response: str
    needs_revision: bool
    iteration_count: int
    # For real-time updates
    supabase_client: Any
    conversation_id: str
    current_steps: List[Dict[str, Any]]

class ReActReasoning:
    """Reflection-based reasoning system - a thinking machine for complex queries."""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model=os.getenv("DEFAULT_LLM", "gpt-4o-mini"),
            temperature=0.7,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        self.max_iterations = 2  # Generate -> Reflect -> Revise (if needed)
        self.workflow = self._create_reflection_workflow()
    
    async def process_with_reasoning(
        self, 
        user_input: str, 
        system_prompt: str,
        conversation_history: List = None,
        supabase_client = None,
        conversation_id: str = None
    ) -> Dict[str, Any]:
        """Process complex query using reflection workflow."""
        
        initial_state = ReflectionState(
            user_input=user_input,
            system_prompt=system_prompt,
            conversation_history=conversation_history or [],
            draft_response="",
            reflection="",
            final_response="",
            needs_revision=False,
            iteration_count=0,
            supabase_client=supabase_client,
            conversation_id=conversation_id or "",
            current_steps=[]
        )
        
        # Run the reflection workflow
        result = await self.workflow.ainvoke(initial_state)
        
        return {
            "reasoning_steps": self._format_reflection_steps(result),
            "final_answer": result["final_response"],
            "step_count": result["iteration_count"],
            "reasoning_used": True
        }
    
    def _create_reflection_workflow(self) -> StateGraph:
        """Create LangGraph workflow for reflection pattern."""
        
        def generate_response(state: ReflectionState) -> ReflectionState:
            """Generate initial response to the query"""
            print("💭 Reflection Step 1: GENERATING")
            
            # Add initial step to show we started thinking
            initial_step = {
                "step": 1,
                "type": "generation_start",
                "content": "Starting to generate response...",
                "timestamp": datetime.now().isoformat()
            }
            self._update_reflection_steps_in_db(state, initial_step)
            
            generate_prompt = self._create_generate_prompt(state)
            response = self.llm.invoke([generate_prompt])
            
            state["draft_response"] = response.content
            state["iteration_count"] += 1
            
            # Update with generation complete
            generation_step = {
                "step": 2,
                "type": "generation",
                "content": f"Initial response generated ({len(response.content)} chars)",
                "timestamp": datetime.now().isoformat()
            }
            self._update_reflection_steps_in_db(state, generation_step)
            
            return state
        
        def reflect_on_response(state: ReflectionState) -> ReflectionState:
            """Reflect on the draft response and identify improvements"""
            print("🤔 Reflection Step 2: REFLECTING")
            
            # Add reflection start step
            reflection_start_step = {
                "step": 3,
                "type": "reflection_start",
                "content": "Analyzing response quality...",
                "timestamp": datetime.now().isoformat()
            }
            self._update_reflection_steps_in_db(state, reflection_start_step)
            
            reflect_prompt = self._create_reflection_prompt(state)
            response = self.llm.invoke([reflect_prompt])
            
            state["reflection"] = response.content
            
            # Simple heuristic: if reflection suggests improvements, revise
            state["needs_revision"] = (
                "improve" in response.content.lower() or 
                "better" in response.content.lower() or
                "missing" in response.content.lower() or
                "add" in response.content.lower()
            )
            
            # Add reflection complete step
            reflection_step = {
                "step": 4,
                "type": "reflection",
                "content": response.content[:200] + "..." if len(response.content) > 200 else response.content,
                "timestamp": datetime.now().isoformat()
            }
            self._update_reflection_steps_in_db(state, reflection_step)
            
            return state
        
        def revise_response(state: ReflectionState) -> ReflectionState:
            """Revise the response based on reflection"""
            print("✨ Reflection Step 3: REVISING")
            
            # Add revision start step
            revision_start_step = {
                "step": 5,
                "type": "revision_start",
                "content": "Improving response based on reflection...",
                "timestamp": datetime.now().isoformat()
            }
            self._update_reflection_steps_in_db(state, revision_start_step)
            
            revise_prompt = self._create_revision_prompt(state)
            response = self.llm.invoke([revise_prompt])
            
            state["final_response"] = response.content
            state["iteration_count"] += 1
            
            # Add revision complete step
            revision_step = {
                "step": 6,
                "type": "revision",
                "content": f"Response revised ({len(response.content)} chars)",
                "timestamp": datetime.now().isoformat()
            }
            self._update_reflection_steps_in_db(state, revision_step)
            
            return state
        
        def finalize_response(state: ReflectionState) -> ReflectionState:
            """Use draft as final if no revision needed"""
            print("✅ Reflection: FINALIZING")
            
            state["final_response"] = state["draft_response"]
            
            # Add finalization step
            finalization_step = {
                "step": 5,
                "type": "finalization",
                "content": "Response approved without revision",
                "timestamp": datetime.now().isoformat()
            }
            self._update_reflection_steps_in_db(state, finalization_step)
            
            return state
        
        def should_revise(state: ReflectionState) -> str:
            """Determine if revision is needed"""
            return "revise" if state["needs_revision"] else "finalize"
        
        # Create workflow
        workflow = StateGraph(ReflectionState)
        
        # Add nodes
        workflow.add_node("generate", generate_response)
        workflow.add_node("reflect", reflect_on_response)
        workflow.add_node("revise", revise_response)
        workflow.add_node("finalize", finalize_response)
        
        # Add edges
        workflow.add_edge("generate", "reflect")
        workflow.add_conditional_edges(
            "reflect",
            should_revise,
            {
                "revise": "revise",
                "finalize": "finalize"
            }
        )
        workflow.add_edge("revise", END)
        workflow.add_edge("finalize", END)
        
        # Set entry point
        workflow.set_entry_point("generate")
        
        return workflow.compile()
    
    def _update_reflection_steps_in_db(self, state: ReflectionState, new_step: Dict[str, Any]):
        """Update the conversation in database with current reflection steps."""
        if not state["supabase_client"] or not state["conversation_id"]:
            return
        
        # Add new step to current steps
        state["current_steps"].append(new_step)
        
        try:
            # Update the conversation record with current reflection steps
            state["supabase_client"].table("conversations").update({
                "reflection_steps": state["current_steps"]
            }).eq("id", state["conversation_id"]).execute()
            
            print(f"🔍 Updated DB with step {new_step['step']}: {new_step['type']}")
        except Exception as e:
            print(f"Error updating reflection steps in DB: {e}")
    
    def _create_generate_prompt(self, state: ReflectionState) -> SystemMessage:
        """Create prompt for initial response generation."""
        
        context = self._format_history(state["conversation_history"])
        
        content = f"""
{state["system_prompt"]}

Contexto da conversa: {context}

Pergunta do usuário: {state["user_input"]}

Responda como uma consultora experiente em uma conversa natural. Seja direta, prática e conversacional - não escreva um relatório formal. Se for algo complexo, organize suas ideias mas mantenha o tom de conversa entre profissionais.
"""
        return SystemMessage(content=content)
    
    def _create_reflection_prompt(self, state: ReflectionState) -> SystemMessage:
        """Create prompt for reflecting on the draft response."""
        
        content = f"""
Você é uma consultora senior revisando uma conversa. Avalie se esta resposta está boa para um cliente:

PERGUNTA: {state["user_input"]}

RESPOSTA DADA:
{state["draft_response"]}

Analise rapidamente:
1. A resposta soa conversacional e natural?
2. Está completa mas não excessivamente formal?
3. É útil e prática para o usuário?
4. Mantém o tom de consultora experiente?

Se vê algo para melhorar (tom muito formal, falta clareza, muito técnico, etc.), mencione usando palavras como "melhorar", "adicionar", "melhor".
Se está boa assim, diga que está adequada.

Avaliação:
"""
        return SystemMessage(content=content)
    
    def _create_revision_prompt(self, state: ReflectionState) -> SystemMessage:
        """Create prompt for revising the response based on reflection."""
        
        content = f"""
{state["system_prompt"]}

PERGUNTA: {state["user_input"]}

RESPOSTA ANTERIOR:
{state["draft_response"]}

FEEDBACK DA REVISÃO:
{state["reflection"]}

Agora melhore a resposta baseada no feedback, mantendo sempre o tom conversacional de consultora experiente. Não transforme em relatório - mantenha como uma conversa natural e prática.

RESPOSTA MELHORADA:
"""
        return SystemMessage(content=content)
    
    def _format_history(self, conversation_history: List) -> str:
        """Format conversation history for context."""
        if not conversation_history:
            return "Nenhuma conversa anterior."
        
        formatted = []
        for msg in conversation_history[-2:]:  # Last 2 messages
            if hasattr(msg, 'content'):
                role = "Usuário" if isinstance(msg, HumanMessage) else "Edith"
                formatted.append(f"{role}: {msg.content[:80]}...")
        
        return " | ".join(formatted)
    
    def _format_reflection_steps(self, final_state: ReflectionState) -> List[Dict[str, Any]]:
        """Format reflection steps as JSONB array for database storage."""
        steps = []
        current_time = datetime.now().isoformat()
        
        if final_state["draft_response"]:
            steps.append({
                "step": 1,
                "type": "generation",
                "content": f"Initial response generated ({len(final_state['draft_response'])} chars)",
                "timestamp": current_time
            })
        
        if final_state["reflection"]:
            steps.append({
                "step": 2,
                "type": "reflection", 
                "content": final_state["reflection"],
                "timestamp": current_time
            })
        
        if final_state["needs_revision"]:
            steps.append({
                "step": 3,
                "type": "revision",
                "content": "Response revised based on reflection",
                "timestamp": current_time
            })
        else:
            steps.append({
                "step": 3,
                "type": "finalization",
                "content": "Response approved without revision",
                "timestamp": current_time
            })
        
        return steps


# Utility function for easy import
async def process_complex_query(
    user_input: str, 
    system_prompt: str, 
    conversation_history: List = None
) -> Dict[str, Any]:
    """Convenience function to process a complex query with reflection reasoning."""
    reasoner = ReActReasoning()
    return await reasoner.process_with_reasoning(user_input, system_prompt, conversation_history)
