from typing import List
from pydantic import BaseModel, Field


class SearchQueryList(BaseModel):
    query: List[str] = Field(
        description="A list of search queries to be used for web research."
    )
    rationale: str = Field(
        description="A brief explanation of why these queries are relevant to the research topic."
    )


class Reflection(BaseModel):
    is_sufficient: bool = Field(
        description="Whether the provided summaries are sufficient to answer the user's question."
    )
    knowledge_gap: str = Field(
        description="A description of what information is missing or needs clarification."
    )
    follow_up_queries: List[str] = Field(
        description="A list of follow-up queries to address the knowledge gap."
    )


class ScholarshipJSON(BaseModel):
    """Single scholarship in JSON format for extraction"""
    title: str = Field(description="Official scholarship title")
    description: str = Field(description="Detailed scholarship description")
    amount: str = Field(description="Award amount with currency symbol")
    deadline: str = Field(description="Application deadline (YYYY-MM-DD)")
    eligibility: str = Field(description="Eligibility criteria")
    requirements: str = Field(description="Application requirements")
    application_url: str = Field(description="Direct application URL")
    provider: str = Field(description="Scholarship provider")
    category: str = Field(description="Scholarship category")


class ScholarshipExtraction(BaseModel):
    """Collection of extracted scholarships with metadata"""
    scholarships: List[ScholarshipJSON] = Field(description="List of extracted scholarships")
    extraction_notes: str = Field(description="Notes about the extraction process")
