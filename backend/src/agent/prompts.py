from datetime import datetime


# Get current date in a readable format
def get_current_date():
    return datetime.now().strftime("%B %d, %Y")


query_writer_instructions = """Your goal is to generate sophisticated and diverse web search queries to find **up to 3 high-quality, active scholarships with direct application links and comprehensive details**. These queries are for an advanced automated web research tool.
The current date is {current_date}. Focus on finding scholarships with deadlines after this date.

Instructions:
- Prefer a single, focused search query if possible. Only add more (up to {number_queries}) if the topic is broad or requires multiple facets to uncover scholarships with specific application details and deadlines.
- Each query should aim to find official scholarship pages, application portals, or detailed announcements.
- Queries should be diverse enough to cover different potential sources for such scholarships.
- Emphasize recency and specificity in your queries to find active opportunities.

Format:
- Format your response as a JSON object with ALL three of these exact keys:
   - "rationale": Brief explanation of why these queries are relevant to finding detailed, active scholarship opportunities.
   - "query": A list of search queries.

Example for finding scholarships:

Topic: Find scholarships for undergraduate computer science students.
```json
{{
    "rationale": "These queries aim to find official scholarship listings, focusing on current opportunities for undergraduate computer science students, and specifically look for application details and deadlines.",
    "query": ["active computer science undergraduate scholarships 2025-2026 application link", "scholarships for CS majors deadline after {current_date} apply online", "undergraduate tech scholarships with application portal {current_date}"]
}}
```

Context: {research_topic}"""


web_searcher_instructions = """Conduct targeted Google Searches to gather the most recent, credible information on "{research_topic}", focusing on finding **active scholarship opportunities with clear deadlines after {current_date} and direct application URLs**. Synthesize findings into a verifiable text artifact.
The current date is {current_date}.

Instructions:
- Prioritize official scholarship pages, application portals, and pages detailing eligibility, deadlines, and application procedures.
- Extract text that specifically mentions application URLs, deadlines, eligibility criteria, and scholarship amounts.
- Consolidate key findings while meticulously tracking the source(s) for each specific piece of information.
- The output should be a summary of relevant text from the search results, rich in details that would help identify complete scholarship entries.
- Only include information found in the search results; do not invent details.

Research Topic:
{research_topic}
"""

reflection_instructions = """You are an expert research assistant analyzing summaries to find **up to 3 high-quality, active scholarships (deadline after {current_date}) with valid, direct application URLs and complete details** about '{research_topic}'.
The current date is {current_date}.

Instructions:
- Analyze the provided summaries. Focus on whether they provide enough detail to extract at least one, and ideally up to 3, complete scholarship entries that meet all criteria (active deadline, valid & direct application URL, and all other fields like amount, eligibility, requirements, provider likely fillable).
- A key knowledge gap is missing or unclear deadlines (not clearly after {current_date}), missing or generic application URLs (not direct to an application page), or insufficient detail for other required fields.
- If promising scholarship leads are found but lack critical details (like a specific application URL or a clear, future deadline), generate specific follow-up queries to find that missing information for those particular leads.
- If the summaries already contain 1-3 strong candidates that seem to meet all criteria, you can deem the information sufficient.

Requirements:
- Ensure any follow-up queries are self-contained and include necessary context for a web search to find the missing pieces for specific scholarship leads.

Output Format:
- Format your response as a JSON object with these exact keys:
   - "is_sufficient": true or false (true if 1-3 strong, complete scholarship candidates are identified).
   - "knowledge_gap": Describe what critical information is missing for promising scholarship leads, or why current leads don't meet the high-quality criteria (e.g., "Missing direct application URL for 'Tech Innovators Scholarship'", "Deadline for 'Future Leaders Grant' is unclear or past {current_date}"). Empty if "is_sufficient" is true.
   - "follow_up_queries": A list of specific questions to address these gaps for identified scholarship leads. Empty if "is_sufficient" is true.

Example:
```json
{{
    "is_sufficient": false,
    "knowledge_gap": "The 'Innovate Grant' summary mentions a 2025 deadline but no specific day or month, and the application URL seems to be a general program page, not the application form itself.",
    "follow_up_queries": ["specific application deadline 2025 Innovate Grant official page", "direct application form URL Innovate Grant"]
}}
```

Reflect carefully on the Summaries to identify knowledge gaps for high-quality scholarship entries and produce your output following this JSON format:

Summaries:
{summaries}
"""

answer_instructions = """Generate a concise summary of the provided information, focusing on details relevant to finding **up to 3 high-quality, active scholarships (deadline after {current_date}) with valid, direct application URLs and complete details** related to the user's question.
The current date is {current_date}.

Instructions:
- You are an intermediate step in a multi-step research process. Your goal is to prepare a summary that will help a subsequent step extract detailed, structured scholarship information.
- Do NOT attempt to format as scholarships yourself in this step (e.g., do not use SCHOLARSHIP_START/END blocks).
- Highlight any specific scholarship names found. For each, explicitly note:
    - Any stated deadline (verifying it's after {current_date}).
    - Any mentioned application website or URL (noting if it seems direct or general).
    - Key eligibility points or amounts if clearly stated.
- Identify if the information points to specific, potentially complete scholarship opportunities or if it's more general.
- If the summaries contain direct quotes or specific data points relevant to scholarship details (amount, eligibility, specific requirements, provider), include them.
- You have access to the user's original research topic.
- You MUST include all relevant citations from the summaries in your summary.

User Context (Original Research Topic):
- {research_topic}

Summaries:
{summaries}"""
