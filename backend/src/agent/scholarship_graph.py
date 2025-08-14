"""
Scholarship-specific LangGraph agent for automated scholarship discovery.
Adapte    f    formatted_prompt = WEB_SEARCH_INSTRUCTIONS.format(
        current_date=current_date,
        research_topic=state["search_query"]
    )tted_prompt = WEB_SEARCH_INSTRUCTIONS.format(
        current_date=current_date,
        research_topic=state["search_query"]
    )om the original graph.py to focus on finding and collecting scholarship information.
"""
import os
import json
import requests
import uuid
from typing import List, Dict, Any
from datetime import datetime
import uuid
import re

from .tools_and_schemas import SearchQueryList, Reflection, ScholarshipJSON, ScholarshipExtraction
from .json_prompts import (
    SCHOLARSHIP_QUERY_INSTRUCTIONS,
    WEB_SEARCH_INSTRUCTIONS, 
    REFLECTION_INSTRUCTIONS,
    SCHOLARSHIP_JSON_EXTRACTION,
    SUMMARY_INSTRUCTIONS,
    get_current_date,
    get_current_iso_date,
)
from dotenv import load_dotenv
from langchain_core.messages import AIMessage
from langgraph.types import Send
from langgraph.graph import StateGraph
from langgraph.graph import START, END
from langchain_core.runnables import RunnableConfig
from google.genai import Client

from .state import (
    OverallState,
    QueryGenerationState,
    ReflectionState,
    WebSearchState,
    ScholarshipData,
    ScholarshipCollection,
)
from .configuration import Configuration
from .prompts import get_current_date
from langchain_google_genai import ChatGoogleGenerativeAI
from .utils import (
    get_citations,
    get_research_topic,
    insert_citation_markers,
    resolve_urls,
)

load_dotenv()

if os.getenv("GEMINI_API_KEY") is None:
    raise ValueError("GEMINI_API_KEY is not set")

# Used for Google Search API
genai_client = Client(api_key=os.getenv("GEMINI_API_KEY"))


def generate_scholarship_queries(state: OverallState, config: RunnableConfig) -> QueryGenerationState:
    """Generate scholarship-specific search queries."""
    print("--- DEBUG: generate_scholarship_queries called! ---")
    configurable = Configuration.from_runnable_config(config)

    if state.get("initial_search_query_count") is None:
        state["initial_search_query_count"] = 3  # Generate more queries

    llm = ChatGoogleGenerativeAI(
        model=configurable.query_generator_model,
        temperature=1.0,
        max_retries=2,
        api_key=os.getenv("GEMINI_API_KEY"),
    )
    structured_llm = llm.with_structured_output(SearchQueryList)

    current_date = get_current_date()
    research_topic = get_research_topic(state["messages"])
    print(f"--- DEBUG: Research topic: {research_topic} ---")
    print(f"--- DEBUG: Number of queries to generate: {state['initial_search_query_count']} ---")
    
    formatted_prompt = SCHOLARSHIP_QUERY_INSTRUCTIONS.format(
        current_date=current_date,
        research_topic=research_topic,
        number_queries=state["initial_search_query_count"],
    )
    
    print(f"--- DEBUG: Query generation prompt: {formatted_prompt[:200]}... ---")
    
    result = structured_llm.invoke(formatted_prompt)
    print(f"--- DEBUG: Generated queries: {result.query} ---")
    
    # Extract just the query strings for search_query state
    query_strings = [q.query if hasattr(q, 'query') else str(q) for q in result.query]
    print(f"--- DEBUG: Extracted query strings: {query_strings} ---")
    
    return {"search_query": query_strings}


def scholarship_web_research(state: WebSearchState, config: RunnableConfig) -> OverallState:
    """Perform scholarship-specific web research."""
    configurable = Configuration.from_runnable_config(config)
    formatted_prompt = WEB_SEARCH_INSTRUCTIONS.format(
        current_date=get_current_date(),
        research_topic=state["search_query"],
    )

    response = genai_client.models.generate_content(
        model=configurable.query_generator_model,
        contents=formatted_prompt,
        config={
            "tools": [{"google_search": {}}],
            "temperature": 0,
        },
    )
    
    # --- START DEBUG LOGIC ---
    print(f"--- DEBUG: Raw scholarship findings for query: '{state['search_query']}' ---")
    if hasattr(response, 'text'):
        print(response.text)
    else:
        print("--- DEBUG: No text found in response ---")
    print(f"--- END DEBUG: Raw scholarship findings for query: '{state['search_query']}' ---")
    # --- END DEBUG LOGIC ---

    resolved_urls = resolve_urls(
        response.candidates[0].grounding_metadata.grounding_chunks, state["id"]
    )
    citations = get_citations(response, resolved_urls)
    # Add a check to ensure citations is a list
    if citations is None:
        citations = []
    modified_text = insert_citation_markers(response.text, citations)
    # Ensure sources_gathered can handle empty citations list
    sources_gathered = [item for citation in citations for item in citation["segments"]] if citations else []

    print(f"--- DEBUG WEB RESEARCH: Returning state with {len(modified_text)} chars of research ---")
    return {
        "sources_gathered": sources_gathered,
        "search_query": [state["search_query"]],
        "web_research_result": [modified_text],
    }


def scholarship_reflection(state: OverallState, config: RunnableConfig) -> ReflectionState:
    """Reflect on scholarship research quality and gaps."""
    configurable = Configuration.from_runnable_config(config)
    state["research_loop_count"] = state.get("research_loop_count", 0) + 1
    # Use reflection_model for reflection
    reasoning_model = state.get("reasoning_model") or configurable.reflection_model

    current_date = get_current_date()
    formatted_prompt = REFLECTION_INSTRUCTIONS.format(
        current_date=current_date,
        research_topic=get_research_topic(state["messages"]),
        summaries="\n\n---\n\n".join(state["web_research_result"]),
    )
    
    llm = ChatGoogleGenerativeAI(
        model=reasoning_model,
        temperature=1.0,
        max_retries=2,
        api_key=os.getenv("GEMINI_API_KEY"),
    )
    result = llm.with_structured_output(Reflection).invoke(formatted_prompt)

    return {
        "is_sufficient": result.is_sufficient,
        "knowledge_gap": result.knowledge_gap,
        "follow_up_queries": result.follow_up_queries,
        "research_loop_count": state["research_loop_count"],
        "number_of_ran_queries": len(state["search_query"]),
    }


def enhanced_scholarship_reflection(state: OverallState, config: RunnableConfig) -> ReflectionState:
    """Enhanced multilayer reflection on scholarship research quality and gaps."""
    configurable = Configuration.from_runnable_config(config)
    state["research_loop_count"] = state.get("research_loop_count", 0) + 1
    reasoning_model = state.get("reasoning_model") or configurable.reflection_model

    current_date = get_current_date()
    formatted_prompt = REFLECTION_INSTRUCTIONS.format(
        current_date=current_date,
        research_topic=get_research_topic(state["messages"]),
        summaries="\n\n---\n\n".join(state["web_research_result"]),
    )
    
    llm = ChatGoogleGenerativeAI(
        model=reasoning_model,
        temperature=1.0,
        max_retries=2,
        api_key=os.getenv("GEMINI_API_KEY"),
    )
    
    try:
        # Try enhanced reflection first
        enhanced_result = llm.with_structured_output(Reflection).invoke(formatted_prompt)
        
        # --- START DEBUG LOGIC ---
        print(f"--- DEBUG: Enhanced reflection results ---")
        print(f"Quality Score: {enhanced_result.quality_metrics.data_quality_score}")
        print(f"Total Scholarships: {enhanced_result.quality_metrics.total_scholarships_found}")
        print(f"Complete Scholarships: {enhanced_result.quality_metrics.complete_scholarships}")
        print(f"Confidence Level: {enhanced_result.confidence_level}")
        print(f"Missing Categories: {enhanced_result.coverage_gaps.missing_categories}")
        print(f"Targeted Queries: {len(enhanced_result.targeted_queries)}")
        print(f"--- END DEBUG: Enhanced reflection results ---")
        # --- END DEBUG LOGIC ---
        
        # Convert enhanced result to compatible format
        follow_up_queries = [tq.query for tq in enhanced_result.targeted_queries]
        
        # Create detailed knowledge gap description
        knowledge_gap = f"Quality Score: {enhanced_result.quality_metrics.data_quality_score:.2f}. "
        knowledge_gap += f"Found {enhanced_result.quality_metrics.total_scholarships_found} total, "
        knowledge_gap += f"{enhanced_result.quality_metrics.complete_scholarships} complete. "
        
        if enhanced_result.coverage_gaps.missing_categories:
            knowledge_gap += f"Missing categories: {', '.join(enhanced_result.coverage_gaps.missing_categories[:3])}. "
        if enhanced_result.coverage_gaps.missing_demographics:
            knowledge_gap += f"Missing demographics: {', '.join(enhanced_result.coverage_gaps.missing_demographics[:3])}. "
        
        knowledge_gap += f"Priority improvements: {', '.join(enhanced_result.improvement_priority[:3])}"
        
        return {
            "is_sufficient": enhanced_result.is_sufficient,
            "knowledge_gap": knowledge_gap,
            "follow_up_queries": follow_up_queries[:5],  # Limit to 5 queries max
            "research_loop_count": state["research_loop_count"],
            "number_of_ran_queries": len(state["search_query"]),
        }
        
    except Exception as e:
        print(f"Enhanced reflection failed, falling back to basic reflection: {e}")
        # Fallback to basic reflection
        basic_result = llm.with_structured_output(Reflection).invoke(
            REFLECTION_INSTRUCTIONS.format(
                current_date=current_date,
                summaries="\n\n---\n\n".join(state["web_research_result"]),
            )
        )
        
        return {
            "is_sufficient": basic_result.is_sufficient,
            "knowledge_gap": basic_result.knowledge_gap,
            "follow_up_queries": basic_result.follow_up_queries,
            "research_loop_count": state["research_loop_count"],
            "number_of_ran_queries": len(state["search_query"]),
        }


def finalize_scholarship_summary(state: OverallState, config: RunnableConfig):
    """Create final scholarship summary and prepare for database insertion."""
    configurable = Configuration.from_runnable_config(config)
    # Use answer_model for final answer generation
    reasoning_model = state.get("reasoning_model") or configurable.answer_model

    current_date = get_current_date()
    
    # Debug the summaries being passed
    summaries_content = "\n---\n\n".join(state["web_research_result"])
    print(f"--- DEBUG: Summaries content length: {len(summaries_content)} ---")
    print(f"--- DEBUG: Number of web research results: {len(state['web_research_result'])} ---")
    print(f"--- DEBUG: First 1000 chars of summaries: {summaries_content[:1000]} ---")
    
    formatted_prompt = SCHOLARSHIP_ANSWER_INSTRUCTIONS.format(
        current_date=current_date,
        summaries=summaries_content,
    )

    llm = ChatGoogleGenerativeAI(
        model=reasoning_model,
        temperature=0,
        max_retries=2,
        api_key=os.getenv("GEMINI_API_KEY"),
    )
    result = llm.invoke(formatted_prompt)

    # --- START DEBUG LOGIC ---
    print(f"--- DEBUG: Final scholarship summary content ---")
    print(f"Content length: {len(result.content)} characters")
    
    # Count scholarship blocks
    scholarship_blocks = result.content.count("SCHOLARSHIP_START")
    print(f"Scholarship blocks found: {scholarship_blocks}")
    
    print("First 500 characters of content:")
    print(result.content[:500])
    print(f"--- END DEBUG: Final scholarship summary content ---")
    # --- END DEBUG LOGIC ---

    # Replace short URLs with original URLs
    unique_sources = []
    for source in state["sources_gathered"]:
        if source["short_url"] in result.content:
            result.content = result.content.replace(
                source["short_url"], source["value"]
            )
            unique_sources.append(source)

    return {
        "messages": [AIMessage(content=result.content)],
        "sources_gathered": unique_sources,
    }


def finalize_scholarship_summary_json(state: OverallState, config: RunnableConfig) -> OverallState:
    """Extract structured scholarship data from web research and convert to JSON format."""
    print("--- DEBUG: finalize_scholarship_summary_json called! ---")
    print(f"--- DEBUG: State keys available: {list(state.keys())} ---")
    
    configurable = Configuration.from_runnable_config(config)
    reasoning_model = state.get("reasoning_model") or configurable.answer_model
    
    # Initialize scholarship collection if not exists
    if "scholarship_collection" not in state:
        state["scholarship_collection"] = ScholarshipCollection()
    
    # Perform web research for each search query if not already done
    web_research_results = state.get("web_research_result", [])
    search_queries = state.get("search_query", [])
    print(f"--- DEBUG: Found {len(search_queries)} search queries: {search_queries} ---")
    print(f"--- DEBUG: Existing web research results: {len(web_research_results)} ---")
    
    if not web_research_results:
        print("--- DEBUG: No existing web research, performing now ---")
        for query in search_queries:
            print(f"--- DEBUG: Researching query: {query} ---")
            
            formatted_prompt = WEB_SEARCH_INSTRUCTIONS.format(
                current_date=get_current_date(),
                research_topic=query,
            )

            response = genai_client.models.generate_content(
                model=configurable.query_generator_model,
                contents=formatted_prompt,
                config={
                    "tools": [{"google_search": {}}],
                    "temperature": 0,
                },
            )
            
            if hasattr(response, 'text') and response.text:
                try:
                    resolved_urls = resolve_urls(
                        response.candidates[0].grounding_metadata.grounding_chunks, str(uuid.uuid4())
                    )
                    citations = get_citations(response, resolved_urls)
                    if citations is None:
                        citations = []
                    modified_text = insert_citation_markers(response.text, citations)
                    web_research_results.append(modified_text)
                    print(f"--- DEBUG: Added research result with {len(modified_text)} chars ---")
                except Exception as e:
                    print(f"--- DEBUG: Error processing grounding metadata: {e}, using raw text ---")
                    web_research_results.append(response.text)
                    print(f"--- DEBUG: Added raw research result with {len(response.text)} chars ---")
            else:
                print(f"--- DEBUG: No response text for query: {query} ---")
        
        # Update state with web research results
        state["web_research_result"] = web_research_results
        state["search_query"] = search_queries
    
    # Combine all web research results
    summaries_content = "\n---\n\n".join(web_research_results)
    print(f"--- DEBUG: Processing {len(summaries_content)} characters of content ---")
    
    if not summaries_content.strip():
        print("--- DEBUG: No web research content to process ---")
        return {"scholarship_collection": state["scholarship_collection"]}
    
    # Use structured LLM to extract scholarships in JSON format
    llm = ChatGoogleGenerativeAI(
        model=reasoning_model,
        temperature=0,
        max_retries=2,
        api_key=os.getenv("GEMINI_API_KEY"),
    )
    
    current_date = get_current_date()
    extraction_prompt = SCHOLARSHIP_JSON_EXTRACTION.format(
        current_date=current_date,
        scholarship_text=summaries_content
    )
    
    try:
        structured_llm = llm.with_structured_output(ScholarshipExtraction)
        extraction_result = structured_llm.invoke(extraction_prompt)
        
        print(f"--- DEBUG: Extracted {len(extraction_result.scholarships)} scholarships ---")
        
        if not extraction_result.scholarships:
            print("--- DEBUG: No scholarships extracted by LLM, checking response ---")
            print(f"--- DEBUG: Response type: {type(extraction_result)} ---")
            
            # Try without structured output to see what the LLM actually returns
            print("--- DEBUG: Trying unstructured extraction for debugging ---")
            unstructured_response = llm.invoke(extraction_prompt)
            print(f"--- DEBUG: Unstructured response content (first 500 chars): {unstructured_response.content[:500]} ---")
        
        # Process each extracted scholarship
        for raw_scholarship in extraction_result.scholarships:
            # Validate and enhance the scholarship data
            if validate_scholarship_quality(raw_scholarship):
                # Auto-categorize if needed
                category = auto_categorize_scholarship(raw_scholarship.title, raw_scholarship.description)
                if not raw_scholarship.category or raw_scholarship.category == "Not available":
                    raw_scholarship.category = category
                
                # Create structured scholarship data
                scholarship_data = ScholarshipData.create_new(
                    title=raw_scholarship.title,
                    description=raw_scholarship.description,
                    amount=raw_scholarship.amount,
                    deadline=raw_scholarship.deadline,
                    eligibility=raw_scholarship.eligibility,
                    requirements=raw_scholarship.requirements,
                    application_url=raw_scholarship.application_url,
                    provider=raw_scholarship.provider,
                    category=raw_scholarship.category
                )
                
                # Set status based on deadline
                scholarship_data.status = "active" if is_active_scholarship(raw_scholarship.deadline) else "expired"
                
                state["scholarship_collection"].add_scholarship(scholarship_data)
                print(f"--- DEBUG: Added scholarship: {scholarship_data.title} ---")
        
        print(f"--- DEBUG: Final collection has {len(state['scholarship_collection'].scholarships)} scholarships ---")
        
    except Exception as e:
        print(f"--- ERROR: Failed to extract structured scholarships: {e} ---")
        print("--- DEBUG: Falling back to legacy text parsing ---")
        # Fallback to legacy parsing if structured extraction fails
        scholarships = parse_legacy_scholarship_format(summaries_content)
        for scholarship in scholarships:
            state["scholarship_collection"].add_scholarship(scholarship)
    
    return {"scholarship_collection": state["scholarship_collection"]}


def search_missing_scholarship_details(state: OverallState, config: RunnableConfig) -> OverallState:
    """Search for missing details for incomplete scholarships."""
    configurable = Configuration.from_runnable_config(config)
    
    # Check for scholarships missing critical information
    incomplete_scholarships = []
    if "scholarship_collection" in state:
        for scholarship in state["scholarship_collection"].scholarships:
            missing_fields = []
            if not scholarship.application_url or scholarship.application_url == "Not available":
                missing_fields.append("application_url")
            if not scholarship.deadline or scholarship.deadline == "Not available":
                missing_fields.append("deadline")
            if not scholarship.amount or scholarship.amount == "Not available":
                missing_fields.append("amount")
            
            if missing_fields:
                incomplete_scholarships.append({
                    "scholarship": scholarship,
                    "missing_fields": missing_fields
                })
    
    if not incomplete_scholarships:
        print("All scholarships have complete information")
        return state
    
    print(f"Found {len(incomplete_scholarships)} scholarships with missing critical information")
    
    # Generate targeted searches for missing information
    additional_searches = []
    for item in incomplete_scholarships[:3]:  # Limit to top 3 to avoid too many searches
        scholarship = item["scholarship"]
        missing = item["missing_fields"]
        
        search_query = f'"{scholarship.title}" {scholarship.provider} application form deadline amount 2025'
        additional_searches.append(search_query)
    
    # Perform additional searches
    if additional_searches:
        print(f"Performing {len(additional_searches)} additional searches for missing scholarship details")
        
        for search_query in additional_searches:
            try:
                # Perform web search (reusing existing logic)
                search_state = {"search_query": search_query, "id": str(uuid.uuid4())}
                search_result = scholarship_web_research(search_state, config)
                
                if "web_research_result" in search_result:
                    state["web_research_result"].extend(search_result["web_research_result"])
            except Exception as e:
                print(f"Error in additional search for '{search_query}': {e}")
    
    return state

def continue_to_scholarship_research(state: OverallState) -> str:
    """Determine if we should continue to scholarship research."""
    return "finalize_scholarship_summary_json"


def evaluate_scholarship_research(state: OverallState) -> str:
    """Evaluate if scholarship research is sufficient or needs more iterations."""
    # Simple logic - if we have enough research loops, finalize
    max_loops = state.get("max_research_loops", 2)
    current_loop = state.get("research_loop_count", 0)
    
    if current_loop >= max_loops:
        return "finalize_scholarship_summary"
    
    # Check if we have sufficient information
    if len(state.get("web_research_result", [])) >= 3:
        return "finalize_scholarship_summary"
    
    # Otherwise continue research
    return "scholarship_web_research"


# Original scholarship answer instructions for text format
SCHOLARSHIP_ANSWER_INSTRUCTIONS = """\
Your sole task is to parse the following text, which contains information about scholarships, and transform it into a structured format.
Your goal is to identify ALL HIGH-QUALITY scholarships that meet the specified criteria below. There is NO LIMIT on the number of scholarships you can extract - prioritize completeness over artificial restrictions.

The current date is {current_date}.

For EACH qualifying scholarship, you MUST output a block of information formatted EXACTLY as follows:

SCHOLARSHIP_START
FIELD_START: Title
[The official title of the scholarship. Must be between 1 and 200 characters. REQUIRED.]
FIELD_END
FIELD_START: Description
[A detailed description of the scholarship, its purpose, and who it's for. Must be between 1 and 2000 characters. REQUIRED.]
FIELD_END
FIELD_START: Amount
[The scholarship amount (e.g., "$10,000", "Varies", "Full Tuition"). Max 50 chars. REQUIRED. If unknown after thorough search of the specific scholarship page, use "Not available".]
FIELD_END
FIELD_START: Deadline
[The application deadline. YYYY-MM-DD format preferred. If month/year, use last day (e.g., "October 2025" -> "2025-10-31"). REQUIRED. CRITICAL: The scholarship deadline MUST be after {current_date}. If the year is ambiguous, assume a year that makes the scholarship active. If the scholarship is clearly expired or if a future deadline cannot be confidently determined, do NOT include this scholarship.]
FIELD_END
FIELD_START: Eligibility Criteria
[Comma-separated list of specific eligibility criteria. E.g., "High school senior, Min 3.0 GPA". REQUIRED. If none found on the specific scholarship page after thorough search, use "Not available".]
FIELD_END
FIELD_START: Requirements
[Comma-separated list of application requirements. E.g., "Application form, Essay". REQUIRED. If none found on the specific scholarship page after thorough search, use "Not available".]
FIELD_END
FIELD_START: Application URL
[CRITICAL REQUIREMENT: The direct URL to the specific scholarship application page or a page with explicit instructions on how to apply. This URL MUST be extracted directly from the web content and MUST lead to a functional application page. Do not provide a general website URL. Must be a valid URL. REQUIRED. If no such specific, functional, and direct application URL is found on the page after thorough checking, do NOT include this scholarship.]
FIELD_END
FIELD_START: Provider
[Name of the scholarship provider. 1-100 chars. REQUIRED. If unknown after thorough search of the specific scholarship page, use "Not available".]
FIELD_END
FIELD_START: Category
[Relevant category (e.g., STEM, Arts). Comma-separated if multiple. REQUIRED. If unknown after thorough search of the specific scholarship page, use "Not available".]
FIELD_END
SCHOLARSHIP_END

CRITICAL OUTPUT RULES:
1.  ONLY STRUCTURED DATA: Your entire response MUST consist ONLY of SCHOLARSHIP_START...SCHOLARSHIP_END blocks.
2.  NO CONVERSATIONAL TEXT: Do NOT include any introductions, summaries, explanations, or any text whatsoever outside the defined blocks.
3.  EXTRACT ALL QUALIFYING SCHOLARSHIPS: From the provided text, identify and output ALL scholarships that meet the criteria. DO NOT limit to 3 or any arbitrary number.
4.  QUALITY REQUIREMENTS: Each scholarship MUST have an active deadline (after {current_date}) AND a valid, direct, and functional Application URL. All other fields must be present (using "Not available" only if genuinely not found).
5.  ALL FIELDS PER SCHOLARSHIP: For each selected scholarship, include ALL `FIELD_START`...`FIELD_END` segments as defined above. Every field is considered REQUIRED.
6.  HANDLING "NOT AVAILABLE": For fields other than Deadline and Application URL (which have stricter rules for inclusion), if information is genuinely not found on the specific scholarship page after thorough search, use "Not available". Only include scholarships where "Not available" is minimal.
7.  ACCURACY & VALIDITY: Extract information as accurately as possible.
    *   DEADLINE: Must be after {current_date}. If not, or if a valid future date cannot be determined, the scholarship must be omitted.
    *   APPLICATION URL: Must be a specific, direct, and functional link to the application. If not available or not valid, the scholarship must be omitted.
8.  COMPREHENSIVE EXTRACTION: Create a separate SCHOLARSHIP_START...SCHOLARSHIP_END block for each qualifying scholarship found in the text.
9.  NO SCHOLARSHIPS FOUND: If the provided text contains no qualifying scholarships according to these rules, your output should be completely empty. Do NOT output messages like "No scholarships found."

Begin processing the text now.
"""

# Utility functions for scholarship processing

def validate_scholarship_quality(scholarship) -> bool:
    """Validate if scholarship meets minimum quality requirements."""
    print(f"--- DEBUG VALIDATION: Checking scholarship: {scholarship.title[:50]}... ---")
    
    # Check required fields
    if not scholarship.title or not scholarship.description:
        print(f"--- DEBUG VALIDATION: FAILED - Missing title or description ---")
        return False
    
    # Check minimum description length
    if len(scholarship.description) < 30:
        print(f"--- DEBUG VALIDATION: FAILED - Description too short ({len(scholarship.description)} chars) ---")
        return False
    
    # Check if deadline is present and in future (basic validation)
    if not scholarship.deadline or scholarship.deadline == "Not available":
        print(f"--- DEBUG VALIDATION: FAILED - Missing or invalid deadline: {scholarship.deadline} ---")
        return False
    
    # Check for valid application URL (more flexible)
    if not scholarship.application_url or scholarship.application_url == "Not available":
        print(f"--- DEBUG VALIDATION: FAILED - Missing or invalid URL: {scholarship.application_url} ---")
        return False
    
    # Allow URLs that start with http/https or contain keywords indicating they need further research
    url_indicators = ["http://", "https://", "website", "official", "application", "apply"]
    has_url_info = any(indicator in scholarship.application_url.lower() for indicator in url_indicators)
    
    if not has_url_info:
        print(f"--- DEBUG VALIDATION: FAILED - No URL information: {scholarship.application_url} ---")
        return False
    
    print(f"--- DEBUG VALIDATION: PASSED - {scholarship.title[:50]}... ---")
    return True


def auto_categorize_scholarship(title: str, description: str) -> str:
    """Automatically categorize scholarship based on title and description."""
    content = f"{title} {description}".lower()
    
    # STEM keywords
    stem_keywords = ["stem", "science", "technology", "engineering", "math", "computer", 
                     "programming", "data", "research", "laboratory", "technical"]
    
    # Arts keywords  
    arts_keywords = ["art", "arts", "music", "creative", "design", "visual", "performing",
                     "theater", "theatre", "dance", "painting", "sculpture"]
    
    # Business keywords
    business_keywords = ["business", "entrepreneurship", "leadership", "management", 
                         "finance", "marketing", "economics"]
    
    # Medical keywords
    medical_keywords = ["medical", "health", "nursing", "pharmacy", "medicine", "healthcare",
                        "doctor", "physician", "dental", "veterinary"]
    
    # Diversity keywords
    diversity_keywords = ["diversity", "minority", "underrepresented", "hispanic", "latino",
                          "african american", "indigenous", "women", "female", "lgbtq"]
    
    # Environmental keywords
    environmental_keywords = ["environmental", "sustainability", "climate", "green", "conservation",
                              "renewable energy", "ecology"]
    
    # Check categories in order of specificity
    if any(keyword in content for keyword in stem_keywords):
        return "STEM"
    elif any(keyword in content for keyword in medical_keywords):
        return "Medical/Health"
    elif any(keyword in content for keyword in arts_keywords):
        return "Arts & Humanities"
    elif any(keyword in content for keyword in business_keywords):
        return "Business & Economics"
    elif any(keyword in content for keyword in diversity_keywords):
        return "Diversity & Inclusion"
    elif any(keyword in content for keyword in environmental_keywords):
        return "Environmental"
    else:
        return "General"


def is_active_scholarship(deadline: str) -> bool:
    """Check if scholarship deadline is in the future."""
    if not deadline or deadline == "Not available":
        return False
    
    try:
        # Parse various date formats
        if re.match(r'\d{4}-\d{2}-\d{2}', deadline):
            deadline_date = datetime.strptime(deadline, '%Y-%m-%d').date()
        elif re.match(r'\d{2}/\d{2}/\d{4}', deadline):
            deadline_date = datetime.strptime(deadline, '%m/%d/%Y').date()
        else:
            # Try to parse other formats
            from dateutil.parser import parse
            deadline_date = parse(deadline).date()
        
        return deadline_date > datetime.now().date()
    except:
        # If we can't parse the date, assume it might be active
        return True


def parse_legacy_scholarship_format(content: str) -> List[ScholarshipData]:
    """Parse scholarships from legacy text format as fallback."""
    scholarships = []
    
    # Split content into scholarship blocks
    blocks = re.split(r'SCHOLARSHIP_START', content)
    
    for block in blocks[1:]:  # Skip first empty block
        if 'SCHOLARSHIP_END' not in block:
            continue
            
        # Extract fields using regex
        title_match = re.search(r'FIELD_START: Title\s*\n(.*?)\nFIELD_END', block, re.DOTALL)
        desc_match = re.search(r'FIELD_START: Description\s*\n(.*?)\nFIELD_END', block, re.DOTALL)
        amount_match = re.search(r'FIELD_START: Amount\s*\n(.*?)\nFIELD_END', block, re.DOTALL)
        deadline_match = re.search(r'FIELD_START: Deadline\s*\n(.*?)\nFIELD_END', block, re.DOTALL)
        eligibility_match = re.search(r'FIELD_START: Eligibility Criteria\s*\n(.*?)\nFIELD_END', block, re.DOTALL)
        requirements_match = re.search(r'FIELD_START: Requirements\s*\n(.*?)\nFIELD_END', block, re.DOTALL)
        url_match = re.search(r'FIELD_START: Application URL\s*\n(.*?)\nFIELD_END', block, re.DOTALL)
        provider_match = re.search(r'FIELD_START: Provider\s*\n(.*?)\nFIELD_END', block, re.DOTALL)
        category_match = re.search(r'FIELD_START: Category\s*\n(.*?)\nFIELD_END', block, re.DOTALL)
        
        # Create scholarship if we have minimum required fields
        if title_match and desc_match:
            try:
                scholarship = ScholarshipData.create_new(
                    title=title_match.group(1).strip(),
                    description=desc_match.group(1).strip(),
                    amount=amount_match.group(1).strip() if amount_match else "Not available",
                    deadline=deadline_match.group(1).strip() if deadline_match else "Not available",
                    eligibility=eligibility_match.group(1).strip() if eligibility_match else "Not available",
                    requirements=requirements_match.group(1).strip() if requirements_match else "Not available",
                    application_url=url_match.group(1).strip() if url_match else "Not available",
                    provider=provider_match.group(1).strip() if provider_match else "Not available",
                    category=category_match.group(1).strip() if category_match else "General"
                )
                scholarships.append(scholarship)
            except Exception as e:
                print(f"Error parsing scholarship block: {e}")
                continue
    
    return scholarships


# Enhanced search for missing application URLs
async def search_missing_application_urls(state: OverallState, config: RunnableConfig) -> OverallState:
    """Search for missing application URLs for scholarships."""
    if "scholarship_collection" not in state:
        return state
    
    configurable = Configuration.from_runnable_config(config)
    
    # Find scholarships with missing or generic URLs
    scholarships_needing_urls = []
    for scholarship in state["scholarship_collection"].scholarships:
        if (not scholarship.application_url or 
            scholarship.application_url == "Not available" or
            is_generic_url(scholarship.application_url)):
            scholarships_needing_urls.append(scholarship)
    
    if not scholarships_needing_urls:
        return state
    
    print(f"--- DEBUG: Searching for URLs for {len(scholarships_needing_urls)} scholarships ---")
    
    # Generate targeted searches for application URLs
    for scholarship in scholarships_needing_urls[:5]:  # Limit to 5 to avoid too many API calls
        try:
            # Create targeted search query
            search_query = f'"{scholarship.title}" "{scholarship.provider}" application form apply online 2025'
            
            # Perform web search
            search_state = {"search_query": search_query, "id": str(uuid.uuid4())}
            search_result = scholarship_web_research(search_state, config)
            
            if "web_research_result" in search_result and search_result["web_research_result"]:
                # Try to extract application URL from results
                url = extract_application_url_from_text(search_result["web_research_result"][0])
                if url and not is_generic_url(url):
                    scholarship.application_url = url
                    print(f"--- DEBUG: Found URL for {scholarship.title}: {url} ---")
        
        except Exception as e:
            print(f"--- ERROR: Failed to search for URL for {scholarship.title}: {e} ---")
    
    return state


def is_generic_url(url: str) -> bool:
    """Check if URL is too generic (homepage, etc.)."""
    if not url or url == "Not available":
        return True
    
    generic_patterns = [
        r'/$',  # Ends with just /
        r'/index\.(html|php)$',  # Index pages
        r'^https?://[^/]+/?$',  # Just domain
    ]
    
    return any(re.search(pattern, url) for pattern in generic_patterns)


def extract_application_url_from_text(text: str) -> str:
    """Extract application URL from search result text."""
    # Look for URLs that contain application-related keywords
    url_pattern = r'https?://[^\s<>"]+(?:apply|application|form|scholarship)[^\s<>"]*'
    urls = re.findall(url_pattern, text, re.IGNORECASE)
    
    if urls:
        return urls[0]  # Return first found application URL
    
    # Fallback: any HTTPS URL
    general_urls = re.findall(r'https://[^\s<>"]+', text)
    if general_urls:
        return general_urls[0]
    
    return "Not available"

async def save_to_google_sheets(state: OverallState, config: RunnableConfig) -> OverallState:
    """Save scholarships to Google Sheets directly."""
    if "scholarship_collection" not in state or not state["scholarship_collection"].scholarships:
        print("--- DEBUG: No scholarships to save ---")
        return state
    
    try:
        # Import Google Sheets libraries
        import gspread
        from google.oauth2.service_account import Credentials
        
        # Setup credentials
        credentials_info = {
            "type": "service_account",
            "client_email": os.environ.get("GOOGLE_SERVICE_ACCOUNT_EMAIL"),
            "private_key": os.environ.get("GOOGLE_PRIVATE_KEY", "").replace("\\n", "\n"),
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "project_id": os.environ.get("GOOGLE_PROJECT_ID", "scholarship-app"),
        }
        
        if not credentials_info["client_email"] or not credentials_info["private_key"]:
            print("--- WARNING: Google Sheets credentials not configured, skipping save ---")
            return state
        
        creds = Credentials.from_service_account_info(
            credentials_info,
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        client = gspread.authorize(creds)
        
        # Open the spreadsheet
        spreadsheet_id = os.environ.get("GOOGLE_SHEETS_ID")
        if not spreadsheet_id:
            print("--- WARNING: GOOGLE_SHEETS_ID not configured, skipping save ---")
            return state
        
        sheet = client.open_by_key(spreadsheet_id).worksheet("Scholarships")
        
        # Track save statistics
        saved_count = 0
        skipped_count = 0
        
        # Get existing data to check for duplicates
        existing_data = sheet.get_all_values()
        existing_titles = set()
        if len(existing_data) > 1:  # Skip header row
            for row in existing_data[1:]:
                if len(row) > 1:  # Make sure row has title
                    existing_titles.add(row[1].lower().strip())  # Title is column B (index 1)
        
        print(f"--- DEBUG: Found {len(existing_titles)} existing scholarships ---")
        
        # Process each scholarship
        for scholarship in state["scholarship_collection"].scholarships:
            # Check for duplicates
            if scholarship.title.lower().strip() in existing_titles:
                print(f"--- DEBUG: Skipping duplicate: {scholarship.title} ---")
                skipped_count += 1
                continue
            
            # Final quality check
            if not validate_scholarship_for_sheets(scholarship):
                print(f"--- DEBUG: Skipping low-quality scholarship: {scholarship.title} ---")
                skipped_count += 1
                continue
            
            # Prepare row data matching Google Sheets columns
            row = [
                scholarship.id,
                scholarship.title,
                scholarship.description,
                scholarship.amount,
                scholarship.deadline,
                scholarship.eligibility,
                scholarship.requirements,
                scholarship.application_url,
                scholarship.provider,
                scholarship.category,
                scholarship.status,
                scholarship.created_date,
                scholarship.modified_date,
                scholarship.created_by,
                scholarship.last_modified_by
            ]
            
            # Append to sheet
            sheet.append_row(row, value_input_option="RAW")
            saved_count += 1
            existing_titles.add(scholarship.title.lower().strip())  # Prevent duplicates in same batch
            
            print(f"--- DEBUG: Saved scholarship: {scholarship.title} ---")
        
        print(f"--- SUMMARY: Saved {saved_count} scholarships, skipped {skipped_count} ---")
        
        # Add metadata to state
        state["scholarships_discovered"] = len(state["scholarship_collection"].scholarships)
        state["scholarships_saved"] = saved_count
        state["scholarships_skipped"] = skipped_count
        
    except Exception as e:
        print(f"--- ERROR: Failed to save to Google Sheets: {e} ---")
        # Don't fail the entire pipeline, just log the error
        state["scholarships_discovered"] = len(state["scholarship_collection"].scholarships) if "scholarship_collection" in state else 0
        state["scholarships_saved"] = 0
        state["save_error"] = str(e)
    
    return state


def validate_scholarship_for_sheets(scholarship: ScholarshipData) -> bool:
    """Final validation before saving to Google Sheets."""
    # Must have title and description
    if not scholarship.title or not scholarship.description:
        return False
    
    # Must have title longer than 5 characters
    if len(scholarship.title) < 5:
        return False
    
    # Must have description longer than 20 characters
    if len(scholarship.description) < 20:
        return False
    
    # Must have valid deadline format or be "Not available"
    if scholarship.deadline and scholarship.deadline != "Not available":
        try:
            # Try to parse the deadline
            if not re.match(r'\d{4}-\d{2}-\d{2}', scholarship.deadline):
                return False
        except:
            pass
    
    # Must have provider
    if not scholarship.provider or scholarship.provider == "Not available":
        return False
    
    return True
# Create the Scholarship Agent Graph
builder = StateGraph(OverallState, config_schema=Configuration)

# Define nodes
builder.add_node("generate_scholarship_queries", generate_scholarship_queries)
builder.add_node("scholarship_web_research", scholarship_web_research)
builder.add_node("scholarship_reflection", scholarship_reflection)
builder.add_node("finalize_scholarship_summary", finalize_scholarship_summary)
builder.add_node("finalize_scholarship_summary_json", finalize_scholarship_summary_json)
builder.add_node("search_missing_scholarship_details", search_missing_scholarship_details)
builder.add_node("search_missing_application_urls", search_missing_application_urls)
builder.add_node("save_to_google_sheets", save_to_google_sheets)

# Set entrypoint
builder.add_edge(START, "generate_scholarship_queries")

# Add conditional edges
builder.add_conditional_edges(
    "generate_scholarship_queries", 
    continue_to_scholarship_research, 
    ["finalize_scholarship_summary_json"]
)

# New JSON-first pipeline flow:
# 1. Generate queries -> 2. JSON extraction (with inline web research) -> 3. Search missing URLs -> 4. Save to sheets
builder.add_edge("finalize_scholarship_summary_json", "search_missing_application_urls")
builder.add_edge("search_missing_application_urls", "save_to_google_sheets")
builder.add_edge("save_to_google_sheets", END)

# Keep legacy text flow for backward compatibility
builder.add_edge("finalize_scholarship_summary", END)

scholarship_graph = builder.compile(name="scholarship-research-agent")
