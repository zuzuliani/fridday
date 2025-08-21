"""
Query Router for Fridday Chatbot
Intelligently routes queries between direct answers and ReAct reasoning
"""

from typing import Dict, Any, Literal
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
import os
import re

QueryRoute = Literal["direct", "react"]

class QueryRouter:
    """Routes queries between direct answers and ReAct reasoning based on complexity."""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model=os.getenv("DEFAULT_LLM", "gpt-4o-mini"),
            temperature=0.1,  # Low temperature for consistent routing
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
    
    def route_query(self, user_input: str, conversation_context: str = "") -> QueryRoute:
        """
        Determine whether a query needs direct answer or ReAct reasoning.
        
        Args:
            user_input: The user's question/message
            conversation_context: Recent conversation context
            
        Returns:
            "direct" for simple queries, "react" for complex analysis
        """
        
        # Quick pattern-based routing for obvious cases
        quick_route = self._quick_pattern_route(user_input)
        if quick_route:
            return quick_route
        
        # Use LLM for more nuanced routing decisions
        return self._llm_route(user_input, conversation_context)
    
    def _quick_pattern_route(self, user_input: str) -> QueryRoute | None:
        """Fast pattern-based routing for obvious cases."""
        
        text = user_input.lower().strip()
        
        # Direct answer patterns (conversational tone)
        direct_patterns = [
            r"\b(olá|oi|hello|hi)\b",  # Greetings
            r"\bse apresent\w*\b",  # Self-introduction requests
            r"\b(obrigad\w*|thank\w*)\b",  # Thanks
            r"\b(como vai|how are you)\b",  # Status questions
            r"\b(quem é você|who are you)\b",  # Identity questions
            r"\b(o que é|what is)\b",  # Simple "what is" questions
            r"\b(como funciona|how does)\b",  # Simple "how does" questions
            r"\b(explica|explain|me conta|tell me)\b",  # Simple explanations
            r"\b(ajuda|help|ajudar)\b.*\b(com|with)\b",  # Help requests
            r"\b(qual|which|que)\b.*\b(melhor|better|recomenda\w*|recommend)\b",  # Simple recommendations
        ]
        
        for pattern in direct_patterns:
            if re.search(pattern, text):
                return "direct"
        
        # ReAct reasoning patterns (only for complex multi-step analysis)
        react_patterns = [
            r"\b(analis\w*|analyz\w*)\b.*\b(competitiv\w*|concorr\w*|mercado completo|market analysis)\b",
            r"\b(desenvolv\w*|criar|create)\b.*\b(estratégia completa|plano detalhado|business case)\b",
            r"\b(swot completa|porter|canvas)\b.*\b(anális\w*|framework)\b",
            r"\b(defin\w*|estabelec\w*)\b.*\b(kpi\w*|métrica\w*)\b.*\b(completo\w*|sistema\w*)\b",
            r"\b(otimiz\w*|reestrutur\w*)\b.*\b(processo\w* completo|operação inteira)\b",
            r"\b(avali\w*|identif\w*)\b.*\b(risco\w* completo|análise de risco)\b",
            r"\b(roadmap|roteiro)\b.*\b(implementação|transformação digital)\b",
            r"\b(plano\w*|estratégia)\b.*\b(entrada.*mercado|expansão|transformação)\b",
        ]
        
        for pattern in react_patterns:
            if re.search(pattern, text):
                return "react"
        
        return None  # Let LLM decide
    
    def _llm_route(self, user_input: str, conversation_context: str) -> QueryRoute:
        """Use LLM to make routing decision for ambiguous cases."""
        
        routing_prompt = SystemMessage(content="""
Você é um roteador para uma consultora de negócios conversacional. Classifique consultas em:

**DIRECT** - Para conversas normais (MAIORIA dos casos):
- Cumprimentos e apresentações
- Perguntas diretas sobre conceitos
- Pedidos de explicação ou esclarecimento  
- Recomendações simples
- Dúvidas pontuais sobre estratégia/gestão
- Qualquer conversa que pode ser respondida naturalmente

**REACT** - APENAS para análises muito complexas e estruturadas:
- Desenvolvimento completo de business cases
- Análises competitivas detalhadas usando frameworks específicos
- Planejamento completo de entrada em mercado
- Reestruturação organizacional complexa  
- Roadmaps de transformação digital completos

PREFIRA SEMPRE "DIRECT" - só use "REACT" para análises muito elaboradas que realmente precisam de múltiplas etapas estruturadas.

Responda APENAS com "DIRECT" ou "REACT".
        """)
        
        user_message = HumanMessage(content=f"""
Contexto da conversa: {conversation_context}

Nova pergunta do usuário: {user_input}

Classificação:""")
        
        try:
            response = self.llm.invoke([routing_prompt, user_message])
            decision = response.content.strip().upper()
            
            if "REACT" in decision:
                return "react"
            else:
                return "direct"
                
        except Exception as e:
            print(f"🔍 Router LLM error: {e}, defaulting to direct")
            # Default to direct if there's an error
            return "direct"
    
    def get_routing_explanation(self, route: QueryRoute, user_input: str) -> str:
        """Get a human-readable explanation of why this route was chosen."""
        
        if route == "direct":
            return "Pergunta simples - resposta direta e conversacional"
        else:
            return "Pergunta complexa - usando análise estruturada com múltiplas etapas"


# Utility functions for easy import
def route_query(user_input: str, conversation_context: str = "") -> QueryRoute:
    """Convenience function to route a single query."""
    router = QueryRouter()
    return router.route_query(user_input, conversation_context)


def should_use_react(user_input: str, conversation_context: str = "") -> bool:
    """Convenience function to check if ReAct reasoning should be used."""
    return route_query(user_input, conversation_context) == "react"
