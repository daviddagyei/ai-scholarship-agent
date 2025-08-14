from __future__ import annotations

from dataclasses import dataclass, field
from typing import TypedDict, List
from pydantic import BaseModel, Field
import uuid
from datetime import datetime

from langgraph.graph import add_messages
from typing_extensions import Annotated


import operator
from dataclasses import dataclass, field
from typing_extensions import Annotated


class ScholarshipData(BaseModel):
    """Schema for individual scholarship data matching Google Sheets columns"""
    id: str = Field(description="Auto-generated unique identifier")
    title: str = Field(description="Official scholarship title")
    description: str = Field(description="Detailed scholarship description")
    amount: str = Field(description="Scholarship amount with currency symbol")
    deadline: str = Field(description="Application deadline (YYYY-MM-DD format)")
    eligibility: str = Field(description="Eligibility criteria")
    requirements: str = Field(description="Application requirements")
    application_url: str = Field(description="Direct URL to application")
    provider: str = Field(description="Scholarship provider/organization")
    category: str = Field(description="Scholarship category (STEM, Arts, etc.)")
    status: str = Field(description="Status: Active, Pending, Expired, Draft, Incomplete")
    created_date: str = Field(description="ISO format creation timestamp")
    modified_date: str = Field(description="ISO format modification timestamp")
    created_by: str = Field(description="Agent identifier")
    last_modified_by: str = Field(description="Last modifier identifier")

    @classmethod
    def create_new(cls, **kwargs) -> 'ScholarshipData':
        """Create a new scholarship with auto-generated metadata"""
        now = datetime.utcnow().isoformat() + 'Z'
        agent_id = "ScholarshipAgent"
        
        return cls(
            id=str(uuid.uuid4()),
            created_date=now,
            modified_date=now,
            created_by=agent_id,
            last_modified_by=agent_id,
            status="Active",  # Default status
            **kwargs
        )


class ScholarshipCollection(BaseModel):
    """Collection of scholarships with metadata"""
    scholarships: List[ScholarshipData] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
    
    def add_scholarship(self, scholarship: ScholarshipData):
        """Add a scholarship to the collection"""
        self.scholarships.append(scholarship)
    
    def to_google_sheets_format(self) -> List[List[str]]:
        """Convert to format suitable for Google Sheets"""
        if not self.scholarships:
            return []
        
        # Header row
        headers = [
            "ID", "Title", "Description", "Amount", "Deadline", "Eligibility", 
            "Requirements", "Application URL", "Provider", "Category", "Status", 
            "Created Date", "Modified Date", "Created By", "Last Modified By"
        ]
        
        # Data rows
        rows = [headers]
        for scholarship in self.scholarships:
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
            rows.append(row)
        
        return rows


class OverallState(TypedDict):
    messages: Annotated[list, add_messages]
    search_query: Annotated[list, operator.add]
    web_research_result: Annotated[list, operator.add]
    sources_gathered: Annotated[list, operator.add]
    scholarship_collection: ScholarshipCollection  # New: JSON-based scholarship collection
    initial_search_query_count: int
    max_research_loops: int
    research_loop_count: int
    reasoning_model: str


class ReflectionState(TypedDict):
    is_sufficient: bool
    knowledge_gap: str
    follow_up_queries: Annotated[list, operator.add]
    research_loop_count: int
    number_of_ran_queries: int


class Query(TypedDict):
    query: str
    rationale: str


class QueryGenerationState(TypedDict):
    query_list: list[Query]


class WebSearchState(TypedDict):
    search_query: str
    id: str


@dataclass(kw_only=True)
class SearchStateOutput:
    running_summary: str = field(default=None)  # Final report
