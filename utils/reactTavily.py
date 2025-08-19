"""
React Tavily Research Tool using LangGraph and LangChain's Tavily integration.

This module provides a React-style research component that uses Tavily's search engine
designed specifically for AI agents to perform real-time web research.
"""

from typing import Dict, Any, List, Optional, TypedDict
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch
from langchain.schema import HumanMessage, SystemMessage, AIMessage
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from pydantic import BaseModel, Field
import os
import json
import asyncio
from datetime import datetime, timezone
from uuid import uuid4


class SourceReference(BaseModel):
    """Individual source reference with metadata."""
    id: str = Field(default_factory=lambda: str(uuid4())[:8])
    title: str
    url: str
    content: str
    snippet: str = ""
    relevance_score: float = Field(default=0.0, ge=0.0, le=1.0)
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class NeedToKnow(BaseModel):
    """Individual research question/topic."""
    id: str = Field(default_factory=lambda: str(uuid4())[:8])
    question: str
    context: str = ""
    priority: int = Field(default=1, ge=1, le=5)
    search_results: List[SourceReference] = Field(default_factory=list)
    analysis: str = ""


class ResearchState(TypedDict):
    """Enhanced state for the research workflow."""
    original_query: str
    need_to_know_questions: List[NeedToKnow]
    all_sources: Dict[str, SourceReference]  # source_id -> SourceReference
    consolidated_analysis: str
    final_report: str
    error: Optional[str]
    metadata: Dict[str, Any]


class ResearchRequest(BaseModel):
    """Request model for research queries."""
    query: str = Field(..., description="The research query to investigate")
    max_results: int = Field(default=5, description="Maximum number of search results")
    topic: str = Field(default="general", description="Topic category for search optimization")
    include_raw_content: bool = Field(default=False, description="Include raw content in results")
    search_depth: str = Field(default="advanced", description="Tavily search depth: 'basic' or 'advanced'")
    include_answer: str = Field(default="advanced", description="Tavily include answer: 'none', 'basic', or 'advanced'")
    verbose: bool = Field(default=False, description="Enable detailed progress logging")


class ResearchResponse(BaseModel):
    """Enhanced response model for research results."""
    query: str
    summary: str
    key_findings: List[str]
    detailed_analysis: str
    sources: List[SourceReference]
    need_to_know_coverage: List[Dict[str, str]]  # question -> summary
    citations_map: Dict[str, str]  # citation_id -> source_id
    raw_results: Optional[List[Dict[str, Any]]] = None
    timestamp: str
    metadata: Dict[str, Any]


class ReactTavilyResearcher:
    """
    Enhanced React-style research component using Tavily and LangGraph.
    
    This class provides a sophisticated research workflow that:
    1. Decomposes queries into "Need to Know" questions
    2. Performs parallel web searches using Tavily
    3. Tracks sources and citations throughout the process
    4. Analyzes and synthesizes results with proper attribution
    5. Returns comprehensive research reports with inline citations
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4", verbose: bool = False):
        """
        Initialize the Enhanced React Tavily Researcher.
        
        Args:
            api_key: Tavily API key (defaults to TAVILY_API_KEY env var)
            model: OpenAI model to use for analysis
            verbose: Enable detailed progress logging by default
        """
        self.verbose = verbose
        # Set up Tavily API key
        if api_key:
            os.environ["TAVILY_API_KEY"] = api_key
        elif not os.getenv("TAVILY_API_KEY"):
            raise ValueError("TAVILY_API_KEY must be provided either as parameter or environment variable")
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model=model,
            temperature=0.3,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Tavily search tool will be created dynamically per request
        
        # Create prompts for different stages
        self._create_prompts()
        
        # Create the enhanced research workflow
        self.workflow = self._create_workflow()
    
    def _get_current_date_context(self) -> str:
        """Get current date context for temporal awareness."""
        now = datetime.now(timezone.utc)
        return f"Current Date: {now.strftime('%B %d, %Y')} (UTC)"
    
    def _log_verbose(self, message: str, emoji: str = "🔧", force: bool = False):
        """Log verbose messages if verbosity is enabled."""
        if self.verbose or force:
            print(f"{emoji} {message}")
    
    def _log_action(self, action: str, status: str = "starting"):
        """Log high-level actions with progress indicators."""
        status_emojis = {
            "starting": "🚀",
            "progress": "⚙️",
            "completed": "✅",
            "error": "❌",
            "thinking": "🤔"
        }
        emoji = status_emojis.get(status, "🔧")
        self._log_verbose(f"{action}", emoji, force=True)
    
    def _log_breakdown(self, title: str, items: List[str], emoji: str = "📋"):
        """Log structured breakdowns like query decomposition."""
        if self.verbose:
            print(f"\n{emoji} {title}")
            print("=" * (len(title) + 4))
            for i, item in enumerate(items, 1):
                print(f"{i}. {item}")
            print()
    
    def _log_thoughts(self, thought: str):
        """Log AI reasoning and decision-making process."""
        if self.verbose:
            print(f"💭 {thought}")
    
    def _log_search_details(self, query: str, enhanced_query: str, results_count: int):
        """Log detailed search information."""
        if self.verbose:
            print(f"\n🔍 Search Details:")
            print(f"   Original: '{query}'")
            if query != enhanced_query:
                print(f"   Enhanced: '{enhanced_query}'")
            print(f"   Results: {results_count} sources found")
            print()
    
    def _create_search_tool(self, max_results: int, search_depth: str, include_answer: str) -> TavilySearch:
        """Create a TavilySearch tool with specified parameters."""
        # Map include_answer string to boolean for TavilySearch
        include_answer_bool = include_answer != "none"
        
        self._log_verbose(f"Creating Tavily search tool: depth={search_depth}, include_answer={include_answer}, max_results={max_results}")
        
        return TavilySearch(
            max_results=max_results,
            search_depth=search_depth,
            include_answer=include_answer_bool
        )
    
    def _enhance_search_query(self, query: str) -> str:
        """Enhance search query with temporal context when appropriate."""
        # Get current year for temporal enhancement
        current_year = datetime.now(timezone.utc).year
        
        # Keywords that indicate need for temporal context
        temporal_keywords = [
            'latest', 'recent', 'current', 'new', 'emerging', 'trending',
            'today', 'now', 'developments', 'updates', 'breakthrough',
            'advances', 'progress', 'state-of-the-art', 'cutting-edge'
        ]
        
        query_lower = query.lower()
        
        # Check if query contains temporal keywords and doesn't already have a year
        needs_temporal_context = (
            any(keyword in query_lower for keyword in temporal_keywords) and
            str(current_year) not in query and
            str(current_year - 1) not in query
        )
        
        if needs_temporal_context:
            # Add current year context to make search more relevant
            enhanced_query = f"{query} {current_year}"
            self._log_verbose(f"Enhanced query: '{query}' → '{enhanced_query}'")
            return enhanced_query
        
        return query
    
    def _create_prompts(self):
        """Create specialized prompts for each workflow stage."""
        
        # Need-to-Know decomposition prompt
        self.decomposition_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert research strategist with temporal awareness. Your task is to break down complex research queries into 3-5 specific "Need to Know" questions that will comprehensively cover the topic.

{current_date}

Instructions:
- Create 3-5 focused, specific questions
- Ensure questions don't overlap significantly
- Cover different aspects/angles of the main query
- Make questions searchable and answerable
- Order by priority (most important first)
- Each question should target specific factual information
- Consider temporal relevance - for queries about "recent," "latest," or "current" topics, focus on information from the past 12-18 months
- For historical queries, be specific about time periods
- Include date ranges in questions when relevant (e.g., "developments in 2024," "trends since 2023")

Format your response as a JSON array of objects with these fields:
- "question": The specific question to research (include relevant date ranges when appropriate)
- "context": Brief context explaining why this question is important and its temporal relevance
- "priority": Integer from 1-5 (1 = highest priority)

Example:
[
  {{
    "question": "What are the latest breakthrough developments in quantum computing in 2024?",
    "context": "Recent developments show the current state of the field and cutting-edge progress",
    "priority": 1
  }}
]"""),
            ("human", "Research Query: {query}\n\nPlease generate 3-5 Need-to-Know questions for this research topic. Format your response as a JSON array.")
        ])
        
        # Individual research analysis prompt
        self.research_analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a research analyst with temporal awareness examining search results for a specific question.

{current_date}

Your task is to:
1. Extract key factual information from the search results
2. Identify the most reliable and relevant sources
3. Note any conflicting information or uncertainties
4. Assess the temporal relevance of the information (how recent/current it is)
5. Provide a clear, concise analysis focusing on facts
6. Prioritize more recent information when analyzing current trends or developments

When referencing information, note which source it comes from by using the source index [1], [2], etc.

Be objective and fact-focused. Highlight any limitations in the available information, including potential outdated information. When analyzing time-sensitive topics, note the publication dates of sources when available."""),
            ("human", "Question: {question}\n\nSearch Results:\n{search_results}\n\nProvide your analysis:")
        ])
        
        # Consolidated analysis prompt
        self.consolidation_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a senior research analyst with temporal awareness tasked with synthesizing research from multiple specialized areas into a comprehensive analysis.

{current_date}

Your task:
1. Integrate findings from all research areas
2. Identify patterns and connections across topics
3. Highlight key insights and implications
4. Note any conflicting information or gaps
5. Maintain proper attribution using source references
6. Assess the temporal relevance and currency of information
7. Distinguish between recent developments and established facts
8. Identify trends and trajectory when analyzing time-sensitive topics

When referencing information, use the format [source_id] to cite sources consistently. Pay special attention to the recency of information and highlight when findings are from recent sources vs. older established knowledge."""),
            ("human", "Original Query: {query}\n\nResearch Areas and Findings:\n{research_findings}\n\nProvide comprehensive analysis:")
        ])
        
        # Report generation prompt
        self.report_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert report writer with temporal awareness creating a comprehensive research report.

{current_date}

Your report should:
1. Start with a clear executive summary
2. Present key findings with proper citations [source_id]
3. Provide detailed analysis with evidence
4. Maintain objectivity and accuracy
5. Highlight any limitations or uncertainties
6. Use clear, professional language
7. Contextualize findings within current timeframe
8. Distinguish between recent developments and established knowledge
9. Note the currency of information and any potential temporal limitations

CRITICAL: Every factual claim must be followed by a citation in the format [source_id]. 
Use the source_id provided in the analysis, not invented numbers.

When discussing recent developments or trends, explicitly mention timeframes and acknowledge the current date context for temporal accuracy.

Structure:
- Executive Summary (with temporal context when relevant)
- Key Findings (with citations and temporal relevance)
- Detailed Analysis (with citations and recency indicators)
- Limitations and Considerations (including temporal limitations)"""),
            ("human", "Query: {query}\n\nConsolidated Analysis:\n{analysis}\n\nAvailable Sources:\n{sources}\n\nGenerate the final report:")
        ])
    
    def _create_workflow(self) -> StateGraph:
        """Create the enhanced LangGraph workflow with Need-to-Know decomposition."""
        
        def decompose_query(state: ResearchState) -> ResearchState:
            """Break down the main query into specific Need-to-Know questions."""
            try:
                query = state["original_query"]
                current_date = self._get_current_date_context()
                
                self._log_action("🧠 Breaking down research query into Need-to-Know questions", "starting")
                self._log_verbose(f"Original Query: '{query}'")
                self._log_verbose(f"Context: {current_date}")
                
                self._log_thoughts("Analyzing query complexity and identifying key research areas...")
                
                # Generate Need-to-Know questions with current date context
                messages = self.decomposition_prompt.format_messages(
                    query=query, 
                    current_date=current_date
                )
                
                self._log_verbose("Invoking LLM for query decomposition...")
                self._log_verbose(f"Formatted messages: {[m.content[:100] for m in messages]}")
                response = self.llm.invoke(messages)
                
                # Parse JSON response
                try:
                    self._log_verbose("Parsing LLM response for Need-to-Know questions...")
                    self._log_verbose(f"Raw LLM response: {response.content[:200]}...")
                    
                    # Try to extract JSON from the response
                    content = response.content.strip()
                    
                    # Look for JSON array in the response
                    import re
                    json_match = re.search(r'\[\s*\{.*?\}\s*\]', content, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(0)
                        self._log_verbose(f"Extracted JSON: {json_str[:100]}...")
                    else:
                        json_str = content
                    
                    questions_data = json.loads(json_str)
                    need_to_know_questions = []
                    
                    if isinstance(questions_data, list):
                        for q_data in questions_data:
                            if isinstance(q_data, dict):
                                need_to_know = NeedToKnow(
                                    question=q_data.get("question", ""),
                                    context=q_data.get("context", ""),
                                    priority=q_data.get("priority", 3)
                                )
                                need_to_know_questions.append(need_to_know)
                    
                    if need_to_know_questions:
                        state["need_to_know_questions"] = need_to_know_questions
                        
                        # Log the breakdown
                        questions_list = [f"[Priority {q.priority}] {q.question}" for q in need_to_know_questions]
                        self._log_breakdown("Need-to-Know Questions Generated", questions_list, "🧠")
                        
                        self._log_action(f"Query decomposition completed - {len(need_to_know_questions)} research areas identified", "completed")
                    else:
                        raise ValueError("No valid questions found in response")
                    
                except (json.JSONDecodeError, ValueError) as e:
                    # Fallback: create a single question from the original query
                    self._log_verbose(f"JSON parsing failed ({str(e)}), creating fallback question...")
                    fallback_question = NeedToKnow(
                        question=query,
                        context="Primary research question",
                        priority=1
                    )
                    state["need_to_know_questions"] = [fallback_question]
                    self._log_action("Using fallback question due to parsing error", "error")
                
            except Exception as e:
                state["error"] = f"Query decomposition error: {str(e)}"
                print(f"❌ Decomposition failed: {str(e)}")
            
            return state
        
        def research_individual_question(state: ResearchState) -> ResearchState:
            """Research each Need-to-Know question in parallel (simulated)."""
            try:
                questions = state.get("need_to_know_questions", [])
                all_sources = state.get("all_sources", {})
                metadata = state.get("metadata", {})
                
                # Get search configuration from request
                max_results = metadata.get("max_results", 5)
                search_depth = metadata.get("search_depth", "advanced")
                include_answer = metadata.get("include_answer", "advanced")
                
                self._log_action(f"🔍 Starting parallel research for {len(questions)} Need-to-Know areas", "starting")
                self._log_thoughts("Each question will be researched individually to ensure comprehensive coverage...")
                
                # Create search tool with current request configuration
                search_tool = self._create_search_tool(max_results, search_depth, include_answer)
                
                for i, question in enumerate(questions, 1):
                    try:
                        self._log_verbose(f"\n--- Research Area {i}/{len(questions)} ---")
                        self._log_verbose(f"Question: {question.question}")
                        self._log_verbose(f"Priority: {question.priority}/5")
                        self._log_verbose(f"Context: {question.context}")
                        
                        # Enhance search query with temporal context if needed
                        self._log_thoughts(f"Analyzing query for temporal context...")
                        enhanced_query = self._enhance_search_query(question.question)
                        
                        self._log_verbose(f"Performing web search with Tavily (depth: {search_depth}, include_answer: {include_answer})...")
                        # Perform search for this specific question
                        search_results = search_tool.invoke(enhanced_query)
                        
                        if not isinstance(search_results, list):
                            search_results = [search_results] if search_results else []
                        
                        # Log search results
                        self._log_search_details(question.question, enhanced_query, len(search_results))
                        
                        # Process and store results
                        self._log_thoughts("Processing and validating search results...")
                        self._log_verbose(f"Raw search results type: {type(search_results)}")
                        
                        processed_sources = []
                        
                        # Handle Tavily's response format
                        for result_item in search_results:
                            if isinstance(result_item, dict):
                                # Check if this is a Tavily response with nested results
                                if 'results' in result_item and isinstance(result_item['results'], list):
                                    self._log_verbose(f"Found Tavily response with {len(result_item['results'])} nested results")
                                    # Process the nested results
                                    for nested_result in result_item['results']:
                                        if isinstance(nested_result, dict):
                                            title = nested_result.get('title', 'Unknown Source')
                                            url = nested_result.get('url', '')
                                            content = nested_result.get('content', '')
                                            
                                            if title and url:
                                                source_ref = SourceReference(
                                                    title=title,
                                                    url=url,
                                                    content=content,
                                                    snippet=content[:300] + "..." if len(content) > 300 else content
                                                )
                                                processed_sources.append(source_ref)
                                                all_sources[source_ref.id] = source_ref
                                                self._log_verbose(f"   ✓ Captured: {source_ref.title[:60]}...")
                                else:
                                    # Handle direct result format
                                    title = result_item.get('title') or result_item.get('name') or 'Unknown Source'
                                    url = result_item.get('url') or result_item.get('link') or ''
                                    content = result_item.get('content') or result_item.get('snippet') or result_item.get('text') or ''
                                    
                                    if title and url:
                                        source_ref = SourceReference(
                                            title=title,
                                            url=url,
                                            content=content,
                                            snippet=content[:300] + "..." if len(content) > 300 else content
                                        )
                                        processed_sources.append(source_ref)
                                        all_sources[source_ref.id] = source_ref
                                        self._log_verbose(f"   ✓ Captured: {source_ref.title[:60]}...")
                                    else:
                                        self._log_verbose(f"   ⚠️ Skipped result - missing title or URL: {result_item.keys()}")
                            else:
                                self._log_verbose(f"   ⚠️ Skipped non-dict result: {type(result_item)}")
                        
                        question.search_results = processed_sources
                        
                        # Analyze results for this question
                        if processed_sources:
                            self._log_thoughts("Analyzing search results for key insights...")
                            formatted_results = []
                            for j, source in enumerate(processed_sources, 1):
                                formatted_results.append(f"""
Source {j} [ID: {source.id}]:
Title: {source.title}
URL: {source.url}
Content: {source.content[:500]}...
""")
                            
                            results_text = "\n".join(formatted_results)
                            
                            # Generate analysis for this specific question with date context
                            self._log_verbose("Invoking LLM for research analysis...")
                            current_date = self._get_current_date_context()
                            messages = self.research_analysis_prompt.format_messages(
                                question=question.question,
                                search_results=results_text,
                                current_date=current_date
                            )
                            
                            analysis_response = self.llm.invoke(messages)
                            question.analysis = analysis_response.content
                            
                            self._log_verbose(f"✅ Research completed for area {i}: {len(processed_sources)} sources analyzed")
                        else:
                            question.analysis = "No reliable sources found for this question."
                            self._log_verbose(f"⚠️ No valid sources found for area {i}")
                    
                    except Exception as e:
                        question.analysis = f"Research failed: {str(e)}"
                        self._log_verbose(f"❌ Research failed for area {i}: {str(e)}")
                
                state["all_sources"] = all_sources
                state["need_to_know_questions"] = questions
                
                self._log_action(f"Individual research completed - {len(all_sources)} total sources gathered across {len(questions)} research areas", "completed")
                
            except Exception as e:
                state["error"] = f"Individual research error: {str(e)}"
                print(f"❌ Individual research failed: {str(e)}")
            
            return state
        
        def consolidate_analysis(state: ResearchState) -> ResearchState:
            """Consolidate all research findings into a comprehensive analysis."""
            try:
                query = state["original_query"]
                questions = state.get("need_to_know_questions", [])
                
                self._log_action("🔄 Consolidating research findings from all areas", "starting")
                self._log_thoughts("Synthesizing insights across multiple research areas to identify patterns and connections...")
                
                # Format research findings
                research_findings = []
                findings_summary = []
                for q in questions:
                    finding = f"""
Research Area: {q.question}
Priority: {q.priority}
Context: {q.context}
Findings: {q.analysis}
Sources Found: {len(q.search_results)}
"""
                    research_findings.append(finding)
                    findings_summary.append(f"[P{q.priority}] {q.question} → {len(q.search_results)} sources")
                
                self._log_breakdown("Research Areas Being Consolidated", findings_summary, "🔄")
                
                findings_text = "\n".join(research_findings)
                
                self._log_thoughts("Invoking LLM to synthesize cross-cutting insights and identify key patterns...")
                
                # Generate consolidated analysis with date context
                current_date = self._get_current_date_context()
                messages = self.consolidation_prompt.format_messages(
                    query=query,
                    research_findings=findings_text,
                    current_date=current_date
                )
                
                self._log_verbose(f"Consolidation inputs - Query: {query[:50]}..., Findings length: {len(findings_text)}")
                self._log_verbose(f"Findings preview: {findings_text[:300]}...")
                response = self.llm.invoke(messages)
                state["consolidated_analysis"] = response.content
                self._log_verbose(f"Consolidation output length: {len(response.content)}")
                self._log_verbose(f"Consolidation preview: {response.content[:200]}...")
                
                self._log_action("Analysis consolidation completed - cross-cutting insights identified", "completed")
                
            except Exception as e:
                state["error"] = f"Consolidation error: {str(e)}"
                state["consolidated_analysis"] = "Failed to consolidate research findings."
                print(f"❌ Consolidation failed: {str(e)}")
            
            return state
        
        def generate_final_report(state: ResearchState) -> ResearchState:
            """Generate the final research report with proper citations."""
            try:
                query = state["original_query"]
                analysis = state.get("consolidated_analysis", "")
                all_sources = state.get("all_sources", {})
                
                self._log_action("📋 Generating final research report with citations", "starting")
                self._log_thoughts("Creating comprehensive report with proper attribution and temporal context...")
                
                # Format sources for the prompt
                sources_text = []
                for source_id, source in all_sources.items():
                    sources_text.append(f"[{source_id}]: {source.title} - {source.url}")
                
                sources_formatted = "\n".join(sources_text)
                
                self._log_verbose(f"Report will include {len(all_sources)} cited sources")
                self._log_thoughts("Ensuring all factual claims include proper [source_id] citations...")
                
                # Generate final report with date context
                current_date = self._get_current_date_context()
                messages = self.report_prompt.format_messages(
                    query=query,
                    analysis=analysis,
                    sources=sources_formatted,
                    current_date=current_date
                )
                
                self._log_verbose("Invoking LLM for final report generation...")
                self._log_verbose(f"Report generation inputs - Query: {query[:50]}..., Analysis length: {len(analysis)}, Sources: {len(all_sources)}")
                self._log_verbose(f"Analysis preview: {analysis[:200]}...")
                self._log_verbose(f"Sources preview: {sources_formatted[:200]}...")
                response = self.llm.invoke(messages)
                state["final_report"] = response.content
                
                self._log_action("Final research report generated with full citations and temporal context", "completed")
                
            except Exception as e:
                state["error"] = f"Report generation error: {str(e)}"
                state["final_report"] = "Failed to generate final report."
                print(f"❌ Report generation failed: {str(e)}")
            
            return state
        
        # Create workflow graph
        workflow = StateGraph(ResearchState)
        
        # Add nodes for the enhanced workflow
        workflow.add_node("decompose_query", decompose_query)
        workflow.add_node("research_questions", research_individual_question)
        workflow.add_node("consolidate_analysis", consolidate_analysis)
        workflow.add_node("generate_final_report", generate_final_report)
        
        # Add edges for the sequential workflow
        workflow.add_edge("decompose_query", "research_questions")
        workflow.add_edge("research_questions", "consolidate_analysis")
        workflow.add_edge("consolidate_analysis", "generate_final_report")
        workflow.add_edge("generate_final_report", END)
        
        # Set entry point
        workflow.set_entry_point("decompose_query")
        
        return workflow.compile()
    
    async def research(self, request: ResearchRequest) -> ResearchResponse:
        """
        Perform enhanced research using the LangGraph workflow.
        
        Args:
            request: Research request with query and parameters
            
        Returns:
            ResearchResponse with structured results and citations
        """
        try:
            # Set verbosity for this request
            original_verbose = self.verbose
            self.verbose = request.verbose or self.verbose
            
            # Prepare initial state for enhanced workflow
            initial_state: ResearchState = {
                "original_query": request.query,
                "need_to_know_questions": [],
                "all_sources": {},
                "consolidated_analysis": "",
                "final_report": "",
                "error": None,
                "metadata": {
                    "max_results": request.max_results,
                    "topic": request.topic,
                    "include_raw_content": request.include_raw_content,
                    "search_depth": request.search_depth,
                    "include_answer": request.include_answer
                }
            }
            
            self._log_action(f"🚀 Starting Enhanced React Tavily Research for: '{request.query}'", "starting")
            if self.verbose:
                print("\n" + "="*80)
                print("🔬 ENHANCED RESEARCH WORKFLOW - VERBOSE MODE")
                print("="*80)
                print(f"🔧 Tavily Configuration:")
                print(f"   • Search Depth: {request.search_depth}")
                print(f"   • Include Answer: {request.include_answer}")
                print(f"   • Max Results per Question: {request.max_results}")
                print()
            
            # Execute enhanced workflow
            final_state = await self.workflow.ainvoke(initial_state)
            
            # Extract and process results
            final_report = final_state.get("final_report", "")
            all_sources = final_state.get("all_sources", {})
            need_to_know_questions = final_state.get("need_to_know_questions", [])
            
            # Process sources into list format
            sources_list = list(all_sources.values())
            
            # Extract key findings from the final report
            key_findings = self._extract_key_findings(final_report)
            
            # Create need-to-know coverage summary
            need_to_know_coverage = []
            for q in need_to_know_questions:
                coverage = {
                    "question": q.question,
                    "summary": q.analysis[:200] + "..." if len(q.analysis) > 200 else q.analysis,
                    "sources_found": str(len(q.search_results))  # Convert to string for validation
                }
                need_to_know_coverage.append(coverage)
            
            # Create citations map (extract [source_id] references from report)
            citations_map = self._extract_citations_map(final_report, all_sources)
            
            # Create summary from final report
            summary = self._extract_summary(final_report)
            
            response = ResearchResponse(
                query=request.query,
                summary=summary,
                key_findings=key_findings,
                detailed_analysis=final_state.get("consolidated_analysis", ""),
                sources=sources_list,
                need_to_know_coverage=need_to_know_coverage,
                citations_map=citations_map,
                raw_results=None,  # Could add raw search results if needed
                timestamp=datetime.now().isoformat(),
                metadata={
                    "sources_count": len(sources_list),
                    "questions_researched": len(need_to_know_questions),
                    "research_date": self._get_current_date_context(),
                    "error": final_state.get("error"),
                    "search_params": {
                        "max_results": request.max_results,
                        "topic": request.topic,
                        "search_depth": request.search_depth,
                        "include_answer": request.include_answer
                    }
                }
            )
            
            # Restore original verbosity
            self.verbose = original_verbose
            
            if request.verbose:
                print(f"\n🎉 RESEARCH COMPLETE!")
                print(f"📊 Results: {len(sources_list)} sources across {len(need_to_know_questions)} research areas")
                print("="*80 + "\n")
            
            return response
            
        except Exception as e:
            # Restore original verbosity on error
            self.verbose = original_verbose
            print(f"❌ Research failed: {str(e)}")
            return ResearchResponse(
                query=request.query,
                summary=f"Research failed: {str(e)}",
                key_findings=[],
                detailed_analysis="",
                sources=[],
                need_to_know_coverage=[],
                citations_map={},
                timestamp=datetime.now().isoformat(),
                metadata={"error": str(e)}
            )
    
    def _extract_key_findings(self, report: str) -> List[str]:
        """Extract key findings from the final report."""
        try:
            # Look for key findings section
            lines = report.split('\n')
            findings = []
            in_findings_section = False
            
            for line in lines:
                line = line.strip()
                if 'key finding' in line.lower() or 'findings' in line.lower():
                    in_findings_section = True
                    continue
                elif in_findings_section:
                    if line.startswith('-') or line.startswith('•') or line.startswith('*'):
                        # Clean up the finding text
                        finding = line.lstrip('-•*').strip()
                        if finding:
                            findings.append(finding)
                    elif line and not line.startswith(' ') and len(findings) > 0:
                        # End of findings section
                        break
            
            # Fallback: extract first few bullet points if no formal findings section
            if not findings:
                for line in lines:
                    line = line.strip()
                    if (line.startswith('-') or line.startswith('•') or line.startswith('*')) and len(line) > 10:
                        finding = line.lstrip('-•*').strip()
                        findings.append(finding)
                        if len(findings) >= 5:  # Limit to 5 findings
                            break
            
            return findings[:5]  # Return max 5 key findings
            
        except Exception:
            return ["Analysis completed - see detailed report for findings"]
    
    def _extract_summary(self, report: str) -> str:
        """Extract executive summary from the final report."""
        try:
            lines = report.split('\n')
            summary_lines = []
            in_summary = False
            
            for line in lines:
                line = line.strip()
                if 'executive summary' in line.lower() or 'summary' in line.lower():
                    in_summary = True
                    continue
                elif in_summary:
                    if line and not line.startswith('#') and len(summary_lines) < 5:
                        summary_lines.append(line)
                    elif line.startswith('#') or 'key finding' in line.lower():
                        break
            
            if summary_lines:
                return ' '.join(summary_lines)
            else:
                # Fallback: return first few sentences
                sentences = report.split('.')[:3]
                return '. '.join(sentences) + '.' if sentences else "Research completed successfully."
                
        except Exception:
            return "Research analysis completed - see detailed report for full findings."
    
    def _extract_citations_map(self, report: str, all_sources: Dict[str, SourceReference]) -> Dict[str, str]:
        """Extract citation references from the report."""
        try:
            citations_map = {}
            # Find all [source_id] patterns in the report
            import re
            citation_pattern = r'\[([a-zA-Z0-9]+)\]'
            matches = re.findall(citation_pattern, report)
            
            for match in matches:
                if match in all_sources:
                    citations_map[match] = match  # citation_id maps to source_id
            
            return citations_map
        except Exception:
            return {}
    
    def research_sync(self, request: ResearchRequest) -> ResearchResponse:
        """
        Synchronous version of enhanced research method.
        
        Args:
            request: Research request with query and parameters
            
        Returns:
            ResearchResponse with structured results and citations
        """
        try:
            # Set verbosity for this request
            original_verbose = self.verbose
            self.verbose = request.verbose or self.verbose
            
            # Prepare initial state for enhanced workflow
            initial_state: ResearchState = {
                "original_query": request.query,
                "need_to_know_questions": [],
                "all_sources": {},
                "consolidated_analysis": "",
                "final_report": "",
                "error": None,
                "metadata": {
                    "max_results": request.max_results,
                    "topic": request.topic,
                    "include_raw_content": request.include_raw_content,
                    "search_depth": request.search_depth,
                    "include_answer": request.include_answer
                }
            }
            
            self._log_action(f"🚀 Starting Enhanced React Tavily Research (Sync) for: '{request.query}'", "starting")
            if self.verbose:
                print("\n" + "="*80)
                print("🔬 ENHANCED RESEARCH WORKFLOW - VERBOSE MODE (SYNCHRONOUS)")
                print("="*80)
            
            # Execute enhanced workflow synchronously
            final_state = self.workflow.invoke(initial_state)
            
            # Extract and process results (same as async version)
            final_report = final_state.get("final_report", "")
            all_sources = final_state.get("all_sources", {})
            need_to_know_questions = final_state.get("need_to_know_questions", [])
            
            sources_list = list(all_sources.values())
            key_findings = self._extract_key_findings(final_report)
            
            need_to_know_coverage = []
            for q in need_to_know_questions:
                coverage = {
                    "question": q.question,
                    "summary": q.analysis[:200] + "..." if len(q.analysis) > 200 else q.analysis,
                    "sources_found": str(len(q.search_results))  # Convert to string for validation
                }
                need_to_know_coverage.append(coverage)
            
            citations_map = self._extract_citations_map(final_report, all_sources)
            summary = self._extract_summary(final_report)
            
            response = ResearchResponse(
                query=request.query,
                summary=summary,
                key_findings=key_findings,
                detailed_analysis=final_state.get("consolidated_analysis", ""),
                sources=sources_list,
                need_to_know_coverage=need_to_know_coverage,
                citations_map=citations_map,
                raw_results=None,
                timestamp=datetime.now().isoformat(),
                metadata={
                    "sources_count": len(sources_list),
                    "questions_researched": len(need_to_know_questions),
                    "research_date": self._get_current_date_context(),
                    "error": final_state.get("error"),
                    "search_params": {
                        "max_results": request.max_results,
                        "topic": request.topic,
                        "search_depth": request.search_depth,
                        "include_answer": request.include_answer
                    }
                }
            )
            
            # Restore original verbosity
            self.verbose = original_verbose
            
            if request.verbose:
                print(f"\n🎉 RESEARCH COMPLETE!")
                print(f"📊 Results: {len(sources_list)} sources across {len(need_to_know_questions)} research areas")
                print("="*80 + "\n")
            
            return response
            
        except Exception as e:
            # Restore original verbosity on error
            self.verbose = original_verbose
            print(f"❌ Research failed: {str(e)}")
            return ResearchResponse(
                query=request.query,
                summary=f"Research failed: {str(e)}",
                key_findings=[],
                detailed_analysis="",
                sources=[],
                need_to_know_coverage=[],
                citations_map={},
                timestamp=datetime.now().isoformat(),
                metadata={"error": str(e)}
            )


# React-style hooks and utilities
class UseResearch:
    """Enhanced React-style hook for research functionality."""
    
    def __init__(self, researcher: ReactTavilyResearcher):
        self.researcher = researcher
        self.loading = False
        self.error = None
        self.data = None
    
    async def research(self, query: str, **kwargs) -> ResearchResponse:
        """Perform enhanced research with loading state management."""
        self.loading = True
        self.error = None
        
        try:
            request = ResearchRequest(query=query, **kwargs)
            self.data = await self.researcher.research(request)
            return self.data
        except Exception as e:
            self.error = str(e)
            raise
        finally:
            self.loading = False


# Factory function for easy instantiation
def create_researcher(api_key: Optional[str] = None, model: str = "gpt-4", verbose: bool = False) -> ReactTavilyResearcher:
    """
    Factory function to create a ReactTavilyResearcher instance.
    
    Args:
        api_key: Tavily API key (optional if set in environment)
        model: OpenAI model to use
        verbose: Enable verbose logging by default
        
    Returns:
        Configured ReactTavilyResearcher instance
    """
    return ReactTavilyResearcher(api_key=api_key, model=model, verbose=verbose)


# Enhanced example usage
if __name__ == "__main__":
    import asyncio
    
    async def main():
        # Create enhanced researcher
        researcher = create_researcher()
        
        # Create research request with verbose mode enabled
        request = ResearchRequest(
            query="Latest breakthroughs in quantum computing 2025",
            max_results=5,
            search_depth="advanced",
            include_answer="advanced",
            include_raw_content=False,
            verbose=True
        )
        
        # Perform enhanced research
        result = await researcher.research(request)
        
        # Print enhanced results
        print("\n" + "="*60)
        print(f"ENHANCED RESEARCH REPORT: {result.query}")
        print("="*60)
        
        print(f"\n📋 EXECUTIVE SUMMARY:")
        print(f"{result.summary}")
        
        print(f"\n🔑 KEY FINDINGS:")
        for i, finding in enumerate(result.key_findings, 1):
            print(f"{i}. {finding}")
        
        print(f"\n🧠 NEED-TO-KNOW COVERAGE:")
        for coverage in result.need_to_know_coverage:
            print(f"• {coverage['question']}")
            print(f"  └─ {coverage['summary']}")
            print(f"  └─ Sources found: {coverage['sources_found']}")
            print()
        
        print(f"\n📚 SOURCES WITH CITATIONS:")
        for i, source in enumerate(result.sources, 1):
            print(f"[{source.id}] {source.title}")
            print(f"    URL: {source.url}")
            print(f"    Snippet: {source.snippet}")
            print()
        
        print(f"\n📊 RESEARCH METADATA:")
        metadata = result.metadata
        print(f"• Total Sources: {metadata.get('sources_count', 0)}")
        print(f"• Research Areas: {metadata.get('questions_researched', 0)}")
        print(f"• Citations Found: {len(result.citations_map)}")
        print(f"• Timestamp: {result.timestamp}")
        
        if result.detailed_analysis:
            print(f"\n📈 DETAILED ANALYSIS:")
            print(result.detailed_analysis[:500] + "..." if len(result.detailed_analysis) > 500 else result.detailed_analysis)
    
    # Run enhanced example
    # asyncio.run(main())
