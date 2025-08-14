"""
JSON-based prompts for scholarship discovery optimized for Google Sheets population.
All prompts are designed to work with structured JSON output for better data quality.
"""

from datetime import datetime
from typing import Dict, Any


def get_current_date():
    """Get current date in a readable format"""
    return datetime.now().strftime("%B %d, %Y")


def get_current_iso_date():
    """Get current date in ISO format"""
    return datetime.utcnow().isoformat() + 'Z'


# Enhanced query generation for scholarship discovery
SCHOLARSHIP_QUERY_INSTRUCTIONS = """Your goal is to generate sophisticated and diverse web search queries to find **high-quality, active scholarships with complete application details** for Google Sheets population.

The current date is {current_date}. Focus on finding scholarships with deadlines after this date.

**Search Strategy:**
- Generate {number_queries} diverse queries to maximize US scholarship discovery
- Target US-specific scholarship names and organizations, not general scholarship websites
- Look for US university financial aid pages with specific scholarship listings
- Target US government, foundation, and corporate scholarship programs with specific details
- Focus on scholarships for US students or international students studying in the US
- Avoid general aggregator sites like scholarships.com, niche.com, fastweb.com

**Target Types:**
- US university-specific scholarships (e.g., "Stanford Knight-Hennessy Scholars application deadline 2025")
- US foundation scholarships (e.g., "Gates Cambridge Scholarship for US students")
- US government programs (e.g., "NSF Graduate Research Fellowship Program application")
- US corporate scholarships (e.g., "Google Computer Science Scholarship US students")
- US professional association awards with specific application details
- State-specific scholarships within the United States
- Scholarships for international students attending US colleges and universities

**Quality Requirements:**
Each query should aim to find US-based scholarships with:
- Clear application deadlines (after {current_date})
- Specific application URLs (not just general info pages)
- Detailed eligibility criteria for US students or students attending US colleges
- Explicit award amounts in US dollars
- Comprehensive application requirements
- Focus on US citizens, permanent residents, or international students studying in the US

Format your response as a JSON object with these exact keys:
- "rationale": Brief explanation of why these queries will find complete scholarship data
- "query": List of {number_queries} search queries

Example:
```json
{{
    "rationale": "These queries target official scholarship databases and specific program pages to find complete scholarship data with application details, focusing on active 2025-2026 opportunities.",
    "query": [
        "US university scholarships 2025-2026 application deadline eligibility amount",
        "American foundation scholarships financial aid current applications open {current_date}",
        "US government scholarship programs undergraduate graduate students apply online 2025"
    ]
}}
```

Research Topic: {research_topic}"""


# Enhanced web search instructions for detailed scholarship extraction
WEB_SEARCH_INSTRUCTIONS = """Conduct comprehensive web searches to find **complete scholarship information** for "{research_topic}" with all details needed for Google Sheets population.

The current date is {current_date}.

**Search Objectives:**
1. Find official US scholarship pages with complete application details
2. Extract structured data for each US-based scholarship found
3. Verify deadlines are after {current_date}
4. Locate direct application URLs (not general information pages)
5. Focus on scholarships for US students or students attending US colleges/universities

**Required Information per Scholarship:**
- **Title**: Official scholarship name
- **Description**: Purpose, goals, target recipients (US focus)
- **Amount**: Exact award amount in US dollars (e.g., $5,000, $10,000)
- **Deadline**: Specific application deadline (YYYY-MM-DD format preferred)
- **Eligibility**: Who can apply (GPA, year level, US citizenship/residency status, demographics)
- **Requirements**: What applicants must submit (essays, transcripts, letters)
- **Application URL**: Direct link to application form or detailed instructions
- **Provider**: US organization offering the scholarship
- **Category**: Field/type (STEM, Arts, Business, Diversity, etc.)

**Quality Standards:**
- Only include scholarships with deadlines after {current_date}
- Prioritize scholarships with direct, functional application URLs
- Focus on scholarships available to US students or students attending US institutions
- Use reasoning to categorize scholarships appropriately
- Extract exact amounts in US dollars when available; use "Varies" or "Up to $X" when ranges given
- Distinguish between eligibility criteria and application requirements
- Exclude international scholarships not applicable to US students or US colleges

**Output Format:**
Provide a comprehensive summary that includes:
1. Each scholarship found with all available details
2. Source URLs for verification
3. Notes on data quality and completeness

Research Topic: {research_topic}"""


# JSON-based reflection instructions
REFLECTION_INSTRUCTIONS = """You are an expert scholarship data analyst reviewing search results for **complete scholarship records** suitable for Google Sheets population.

Current date: {current_date}

**Evaluation Criteria:**
Analyze the provided summaries to determine if they contain enough information to create complete scholarship records with these required fields:
- Title (official name)
- Description (detailed purpose)
- Amount (with currency symbol)
- Deadline (after {current_date}, specific date)
- Eligibility (who can apply)
- Requirements (what to submit)
- Application URL (direct, functional link)
- Provider (organization name)
- Category (reasoned categorization)

**Quality Thresholds:**
- **High Quality**: Has all required fields with specific, actionable information
- **Medium Quality**: Has most fields but missing 1-2 non-critical details
- **Low Quality**: Missing critical fields (deadline, application URL, or amount)

**Decision Logic:**
- If 1+ high-quality scholarships found: Mark as sufficient
- If promising leads found but missing critical data: Request targeted follow-up searches
- Focus follow-up searches on specific scholarship names to find missing application URLs or exact deadlines

Output format (JSON):
```json
{{
    "is_sufficient": true/false,
    "knowledge_gap": "Description of missing critical information",
    "follow_up_queries": ["Specific searches for identified scholarship names with missing data"]
}}
```

Summaries to analyze:
{summaries}"""


# JSON-based scholarship extraction and formatting
SCHOLARSHIP_JSON_EXTRACTION = """You are a US scholarship data extraction specialist. Convert the provided text into structured JSON format for Google Sheets population, focusing specifically on scholarships for US students or students attending US colleges and universities.

Current date: {current_date}

**Extraction Instructions:**
1. Identify ALL qualifying US-based scholarships in the provided text
2. For each scholarship, extract and reason through all required fields
3. Apply quality filters: deadline after {current_date}, functional application URL required, US relevance
4. Use analytical reasoning to fill missing fields when possible
5. Generate properly formatted JSON output
6. EXCLUDE scholarships that are not relevant to US students or US institutions

**US-Specific Focus:**
- Prioritize scholarships for US citizens, permanent residents, and international students studying in the US
- Include state-specific scholarships within the United States
- Include scholarships from US universities, foundations, corporations, and government agencies
- Exclude scholarships that require study outside the US (unless specifically for US students studying abroad)
- Focus on amounts in US dollars

**Field Extraction Guidelines:**

**Title**: Extract official scholarship name (1-200 characters)

**Description**: Comprehensive description including purpose, target audience, and benefits (1-2000 characters)

**Amount**: 
- Include US dollar symbol (e.g., $5,000, $10,000, $25,000)
- Use "Up to $X" or "$X-$Y" for ranges
- Use "Full tuition" or "Varies" when appropriate
- If genuinely unknown after thorough analysis: "Amount not specified"

**Deadline**: 
- YYYY-MM-DD format preferred
- Must be after {current_date}
- If month/year only: use last day of month
- If unclear year: assume next occurrence that makes it active

**Eligibility**: 
- Comma-separated specific criteria with US focus
- Include GPA, academic level, demographics, US citizenship/residency status, field of study
- Example: "US citizens and permanent residents, Undergraduate students, 3.0 GPA minimum, STEM majors"

**Requirements**: 
- Comma-separated application materials needed
- Example: "Application form, Essay (500 words), Transcript, Two letters of recommendation"

**Application URL**: 
- CRITICAL: Must be direct link to application or detailed application instructions
- Not general program information pages
- Must be functional and specific

**Provider**: 
- Official US organization/foundation name
- Example: "National Science Foundation", "Gates Foundation", "University of California", "Coca-Cola Scholars Foundation"

**Category**: 
- Use reasoning to categorize appropriately
- Options: STEM, Arts, Business, Social Sciences, Medical/Health, Diversity, General, Field-specific
- Can be multiple: "STEM, Diversity"

**Status Determination:**
- "Active": Has future deadline and application URL
- "Incomplete": Missing critical application information
- Skip scholarships that don't meet minimum quality threshold

**Output Format:**
```json
{{
    "scholarships": [
        {{
            "title": "Scholarship Name",
            "description": "Detailed description...",
            "amount": "$5,000",
            "deadline": "2025-12-31",
            "eligibility": "Undergraduate students, 3.0 GPA minimum",
            "requirements": "Application form, Essay, Transcript",
            "application_url": "https://example.com/apply",
            "provider": "Example Foundation",
            "category": "STEM"
        }}
    ],
    "extraction_notes": "Summary of extraction process and any issues"
}}
```

**Critical Rules:**
1. Only include scholarships with deadlines after {current_date}
2. Only include scholarships with valid, direct application URLs
3. Use reasoning to complete fields when information is available in context
4. If a field is genuinely unavailable after thorough analysis, note it appropriately
5. Extract ALL qualifying scholarships found in the text

Begin extraction from the following text:

{scholarship_text}"""


# Summary instructions for intermediate processing
SUMMARY_INSTRUCTIONS = """Generate a comprehensive summary of scholarship information found, optimized for subsequent JSON extraction.

Current date: {current_date}

**Summarization Goals:**
1. Preserve all scholarship details found in search results
2. Organize information by individual scholarships
3. Maintain source attribution for verification
4. Highlight complete vs incomplete information

**Information to Preserve:**
- Scholarship names and official titles
- Award amounts with currency
- Application deadlines (verify they're after {current_date})
- Eligibility requirements and criteria
- Application requirements and materials needed
- Application URLs and contact information
- Provider organizations
- Program descriptions and purposes

**Organization Approach:**
- Group information by individual scholarships when possible
- Clearly separate different scholarships found
- Note when information seems to refer to the same scholarship from multiple sources
- Preserve specific details like exact amounts, dates, and URLs

**Quality Indicators:**
- Mark scholarships with complete information (all key fields present)
- Note scholarships with missing critical information (application URL, deadline, etc.)
- Highlight scholarships that appear to have active applications

Original Research Topic: {research_topic}

Source summaries to process:
{summaries}"""
