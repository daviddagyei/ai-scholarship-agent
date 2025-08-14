"""
Scholarship Agent Service
Integrates the LangGraph scholarship agent with the existing Google Sheets backend
"""
import os
import json
import requests
import logging
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
import re

try:
    from dateutil.parser import parse as parse_date
except ImportError:
    # Fallback if dateutil is not available
    def parse_date(date_string):
        return datetime.strptime(date_string, '%Y-%m-%d')

from google.oauth2 import service_account
from googleapiclient.discovery import build
from langchain_core.messages import HumanMessage

# Import the scholarship-specific graph
from .scholarship_graph import scholarship_graph


class ScholarshipAgentService:
    """Service for running scholarship discovery agent and managing results."""
    
    def __init__(self, backend_api_url: str = "http://localhost:5001", 
                 sheets_integration: bool = True):
        self.backend_api_url = backend_api_url
        self.sheets_integration = sheets_integration
        self.logger = self._setup_logging()
        self.agent_auth_token = os.getenv("AGENT_AUTH_TOKEN")
        if not self.agent_auth_token:
            self.logger.warning("AGENT_AUTH_TOKEN not found in environment. API calls to secured endpoints will likely fail.")
        
        # Google Sheets setup (if direct integration is preferred)
        if sheets_integration:
            self._setup_sheets_client()
    
    def _setup_logging(self):
        """Setup logging for the service."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def _setup_sheets_client(self):
        """Setup Google Sheets client for direct integration."""
        try:
            # Use environment variables for Google Sheets credentials
            if os.getenv("GOOGLE_SERVICE_ACCOUNT_EMAIL") and os.getenv("GOOGLE_PRIVATE_KEY"):
                credentials = service_account.Credentials.from_service_account_info({
                    "type": "service_account",
                    "client_email": os.getenv("GOOGLE_SERVICE_ACCOUNT_EMAIL"),
                    "private_key": os.getenv("GOOGLE_PRIVATE_KEY").replace('\\n', '\n'),
                    "token_uri": "https://oauth2.googleapis.com/token",
                }, scopes=['https://www.googleapis.com/auth/spreadsheets'])
                
                self.sheets_service = build('sheets', 'v4', credentials=credentials)
                self.spreadsheet_id = os.getenv("GOOGLE_SHEETS_ID")
                self.logger.info("Google Sheets client initialized successfully")
            else:
                self.logger.warning("Google Sheets credentials not found, using API integration only")
                self.sheets_service = None
        except Exception as e:
            self.logger.error(f"Failed to setup Google Sheets client: {e}")
            self.sheets_service = None
    
    async def discover_scholarships(self, search_criteria: str = "current scholarships for college students 2025") -> Dict[str, Any]:
        """
        Run the scholarship discovery agent with specified search criteria.
        
        Args:
            search_criteria: The search topic/criteria for scholarship discovery
            
        Returns:
            Dictionary containing discovered scholarships and metadata
        """
        try:
            self.logger.info(f"Starting scholarship discovery for: {search_criteria}")
            
            # Prepare the input message
            input_messages = [HumanMessage(content=search_criteria)]
            
            # Run the scholarship agent with the JSON pipeline
            result = await scholarship_graph.ainvoke(
                {"messages": input_messages},
                config={"configurable": {"thread_id": f"scholarship_discovery_{datetime.now().isoformat()}"}}
            )
            
            # Debug: Print all result keys
            self.logger.info(f"DEBUG: Result keys: {list(result.keys())}")
            
            # Extract scholarship collection
            scholarship_collection = result.get("scholarship_collection")
            if scholarship_collection and hasattr(scholarship_collection, 'scholarships'):
                scholarships_data = [
                    {
                        "id": s.id,
                        "title": s.title,
                        "description": s.description,
                        "amount": s.amount,
                        "deadline": s.deadline,
                        "eligibility": s.eligibility,
                        "requirements": s.requirements,
                        "applicationUrl": s.application_url,
                        "provider": s.provider,
                        "category": s.category,
                        "status": s.status,
                        "createdDate": s.created_date,
                        "modifiedDate": s.modified_date,
                        "createdBy": s.created_by,
                        "lastModifiedBy": s.last_modified_by
                    }
                    for s in scholarship_collection.scholarships
                ]
                
                # Return structured response
                return {
                    "success": True,
                    "scholarships": scholarships_data,
                    "scholarships_discovered": len(scholarships_data),
                    "scholarships_saved": result.get("scholarships_saved", len(scholarships_data)),
                    "scholarships_skipped": result.get("scholarships_skipped", 0),
                    "search_criteria": search_criteria,
                    "timestamp": datetime.now().isoformat(),
                    "sources": result.get("sources_gathered", [])
                }
            else:
                self.logger.warning("No scholarship collection found in result")
                return {
                    "success": False,
                    "error": "No scholarships found",
                    "scholarships": [],
                    "scholarships_discovered": 0,
                    "scholarships_saved": 0
                }
                
        except Exception as e:
            self.logger.error(f"Error during scholarship discovery: {e}")
            return {
                "success": False,
                "error": str(e),
                "scholarships": [],
                "scholarships_discovered": 0,
                "scholarships_saved": 0
            }
            
            # Extract and parse the results
            raw_content = result["messages"][-1].content if result["messages"] and result["messages"][-1] else None
            scholarship_summary = raw_content if raw_content is not None else ""
            sources = result.get("sources_gathered", [])
            
            # Debug: Show what content we have
            self.logger.info(f"DEBUG: Raw content length: {len(scholarship_summary) if scholarship_summary else 0}")
            self.logger.info(f"DEBUG: First 500 chars of raw content: {scholarship_summary[:500] if scholarship_summary else 'No content'}")
            
            # Check for new JSON format first (scholarship_collection)
            scholarships = []
            if "scholarship_collection" in result and result["scholarship_collection"]:
                # New JSON format
                collection = result["scholarship_collection"]
                if hasattr(collection, 'scholarships'):
                    scholarships = [self._scholarship_data_to_dict(s) for s in collection.scholarships]
                else:
                    # Handle case where it's already a dict
                    scholarships = collection.get("scholarships", [])
                self.logger.info(f"Found {len(scholarships)} scholarships from JSON collection")
            else:
                # Fallback to parsing from summary text (old format) and convert to JSON
                parsed_scholarships = self._parse_scholarships_from_summary(scholarship_summary)
                scholarships = [self._scholarship_dict_to_json_format(s) for s in parsed_scholarships]
                self.logger.info(f"Parsed and converted {len(scholarships)} scholarships from summary text to JSON")
            
            self.logger.info(f"Discovered {len(scholarships)} scholarships")
            
            return {
                "scholarships": scholarships,
                "summary": scholarship_summary,
                "sources": sources,
                "search_criteria": search_criteria,
                "discovery_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error during scholarship discovery: {e}")
            raise
    
    def _parse_scholarships_from_summary(self, summary: str) -> List[Dict[str, Any]]:
        """
        Parse individual scholarships from the agent's summary text
        using SCHOLARSHIP_START/END and FIELD_START/END delimiters.
        """
        scholarships = []
        
        # Regex to find individual scholarship blocks
        scholarship_blocks = re.findall(r"SCHOLARSHIP_START(.*?)SCHOLARSHIP_END", summary, re.DOTALL)
        
        for block in scholarship_blocks:
            scholarship_data = {
                'title': '',
                'provider': '',
                'amount': '',
                'deadline': '',
                'eligibility': '',
                'requirements': '', # Added this field
                'url': '',
                'category': 'General', # Default category
                'status': 'active',    # Default status
                'created_date': datetime.now().strftime('%Y-%m-%d'),
                'modified_date': datetime.now().strftime('%Y-%m-%d'),
                'created_by': 'scholarship-agent',
                'last_modified_by': 'scholarship-agent',
                'description': '' # Will be populated if specific fields are missing but block has text
            }
            
            # Extract fields within the block
            name_provider_match = re.search(r"FIELD_START: Name and Provider(.*?)FIELD_END", block, re.DOTALL)
            if name_provider_match:
                # Attempt to split Name and Provider; this might need refinement
                # Assuming "Name - Provider" or "Name by Provider" or "Name (Provider)"
                name_provider_text = name_provider_match.group(1).strip()
                # Simple split, might need a more robust way if format varies
                parts = re.split(r' - | by | @ | provided by ', name_provider_text, 1, re.IGNORECASE)
                if len(parts) > 1:
                    scholarship_data['title'] = parts[0].strip()
                    scholarship_data['provider'] = parts[1].strip()
                else:
                    scholarship_data['title'] = name_provider_text # If no clear provider, assign all to title
            
            amount_match = re.search(r"FIELD_START: Award Amount(.*?)FIELD_END", block, re.DOTALL)
            if amount_match:
                scholarship_data['amount'] = amount_match.group(1).strip()
            
            deadline_match = re.search(r"FIELD_START: Deadline(.*?)FIELD_END", block, re.DOTALL)
            if deadline_match:
                scholarship_data['deadline'] = deadline_match.group(1).strip()
            
            eligibility_match = re.search(r"FIELD_START: Eligibility(.*?)FIELD_END", block, re.DOTALL)
            if eligibility_match:
                scholarship_data['eligibility'] = eligibility_match.group(1).strip()

            requirements_match = re.search(r"FIELD_START: Application Requirements(.*?)FIELD_END", block, re.DOTALL)
            if requirements_match:
                scholarship_data['requirements'] = requirements_match.group(1).strip()
            
            url_match = re.search(r"FIELD_START: Source URL(.*?)FIELD_END", block, re.DOTALL)
            if url_match:
                # Extract the first http/https URL found in the field
                url_search = re.search(r'(https?://\\S+)', url_match.group(1).strip())
                if url_search:
                    scholarship_data['url'] = url_search.group(1)

            # If title is still empty, try to get it from a general "Name" or "Title" field if present
            if not scholarship_data['title']:
                title_match = re.search(r"FIELD_START: Name(.*?)FIELD_END", block, re.DOTALL) or \
                              re.search(r"FIELD_START: Title(.*?)FIELD_END", block, re.DOTALL)
                if title_match:
                    scholarship_data['title'] = title_match.group(1).strip()
            
            # Basic description from the block if other fields are sparse
            # This creates a simple description from the raw block content, excluding the delimiters
            cleaned_block = block
            for field_marker in re.findall(r"FIELD_START:.*FIELD_END", cleaned_block, re.DOTALL):
                cleaned_block = cleaned_block.replace(field_marker, "")
            scholarship_data['description'] = cleaned_block.strip()


            if scholarship_data.get('title'): # Only add if a title was successfully parsed
                scholarships.append(scholarship_data)
            else:
                self.logger.warning(f"Could not parse a title for scholarship block: {block[:100]}...") # Log if no title
        
        return scholarships
    
    def save_scholarships_via_api(self, scholarships: List[Dict[str, Any]]) -> int:
        """Save scholarships to the database via the backend API."""
        saved_count = 0
        if not self.agent_auth_token:
            self.logger.error("AGENT_AUTH_TOKEN is not set. Cannot save scholarships via API.")
            return 0

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.agent_auth_token}"
        }
        
        for scholarship in scholarships:
            try:
                # Ensure essential fields are present
                if not scholarship.get('title') or not scholarship.get('amount') or not scholarship.get('deadline'):
                    self.logger.warning(f"Skipping scholarship due to missing essential fields (title, amount, or deadline): {scholarship.get('title', 'N/A')}")
                    continue

                payload = {
                    "title": scholarship.get('title'),
                    "description": scholarship.get('description', scholarship.get('eligibility', 'No description provided.')), # Use eligibility if desc is empty
                    "amount": scholarship.get('amount'),
                    "deadline": scholarship.get('deadline'),
                    "eligibility": scholarship.get('eligibility', 'Not specified'),
                    "url": scholarship.get('url', ''),
                    "provider": scholarship.get('provider', 'Not specified'),
                    "requirements": scholarship.get('requirements', 'Not specified'),
                    "category": scholarship.get('category', 'General'),
                    "status": scholarship.get('status', 'active'),
                    # Fields like created_date, created_by are usually handled by the backend
                }
                
                response = requests.post(
                    f"{self.backend_api_url}/api/admin/scholarships", 
                    json=payload,
                    headers=headers
                )
                
                if response.status_code == 201:
                    self.logger.info(f"Successfully saved scholarship: {scholarship.get('title')}")
                    saved_count += 1
                else:
                    self.logger.error(f"Failed to save scholarship {scholarship.get('title')}: {response.status_code} - {response.text}")
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Error saving scholarship {scholarship.get('title')}: {e}")
            except Exception as e:
                self.logger.error(f"Unexpected error processing scholarship {scholarship.get('title')} for API save: {e}")
        return saved_count
    
    def save_scholarships_direct(self, scholarships: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Save scholarships directly to Google Sheets.
        
        Args:
            scholarships: List of scholarship dictionaries
            
        Returns:
            List of saved scholarship data
        """
        if not self.sheets_service or not self.spreadsheet_id:
            self.logger.error("Google Sheets service not available")
            return []
        
        saved_scholarships = []
        
        for scholarship in scholarships:
            try:
                # Prepare row data according to your sheet structure
                row_data = [
                    "",  # ID - will be auto-generated
                    scholarship.get('title', ''),
                    scholarship.get('description', ''),
                    scholarship.get('amount', ''),
                    scholarship.get('deadline', ''),
                    scholarship.get('eligibility', ''),
                    scholarship.get('requirements', ''),
                    scholarship.get('url', ''),
                    scholarship.get('provider', ''),
                    scholarship.get('category', 'General'),
                    scholarship.get('status', 'active'),
                    scholarship.get('created_date', datetime.now().strftime('%Y-%m-%d')),
                    scholarship.get('modified_date', datetime.now().strftime('%Y-%m-%d')),
                    scholarship.get('created_by', 'scholarship-agent'),
                    scholarship.get('last_modified_by', 'scholarship-agent')
                ]
                
                # Append to sheet
                result = self.sheets_service.spreadsheets().values().append(
                    spreadsheetId=self.spreadsheet_id,
                    range='Scholarships!A:O',
                    valueInputOption='RAW',
                    body={'values': [row_data]}
                ).execute()
                
                saved_scholarships.append({
                    'scholarship': scholarship,
                    'sheet_result': result
                })
                
                self.logger.info(f"Saved scholarship to sheet: {scholarship.get('title', 'Unknown')}")
                
            except Exception as e:
                self.logger.error(f"Error saving scholarship to sheet {scholarship.get('title', 'Unknown')}: {e}")
        
        return saved_scholarships
    
    async def run_daily_discovery(self, search_criteria: Optional[str] = None) -> Dict[str, Any]:
        """
        Run the daily scholarship discovery process with automatic Google Sheets integration.
        
        Args:
            search_criteria: Optional custom search criteria
            
        Returns:
            Summary of the discovery process with detailed statistics
        """
        if not search_criteria:
            # Default search criteria for daily runs targeting current opportunities
            current_year = datetime.now().year
            search_criteria = f"new scholarships and financial aid opportunities for college students {current_year} with application deadlines"
        
        try:
            self.logger.info(f"Starting daily scholarship discovery: {search_criteria}")
            start_time = datetime.now()
            
            # Run the discovery using the JSON-first pipeline
            discovery_result = await self.discover_scholarships(search_criteria)
            
            if not discovery_result.get("success", False):
                return {
                    "success": False,
                    "error": discovery_result.get("error", "Discovery failed"),
                    "scholarships_discovered": 0,
                    "scholarships_saved": 0,
                    "scholarships_skipped": 0,
                    "timestamp": datetime.now().isoformat(),
                    "duration_seconds": (datetime.now() - start_time).total_seconds()
                }
            
            # Get results from discovery
            scholarships = discovery_result.get("scholarships", [])
            scholarships_discovered = len(scholarships)
            scholarships_saved = discovery_result.get("scholarships_saved", 0)
            scholarships_skipped = discovery_result.get("scholarships_skipped", 0)
            
            self.logger.info(f"Discovery completed: {scholarships_discovered} found, {scholarships_saved} saved, {scholarships_skipped} skipped")
            
            # Calculate duration
            end_time = datetime.now()
            duration_seconds = (end_time - start_time).total_seconds()
            
            # Prepare comprehensive summary
            summary_result = {
                "success": True,
                "scholarships_discovered": scholarships_discovered,
                "scholarships_saved": scholarships_saved,
                "scholarships_skipped": scholarships_skipped,
                "search_criteria": search_criteria,
                "timestamp": end_time.isoformat(),
                "duration_seconds": duration_seconds,
                "sources_count": len(discovery_result.get("sources", [])),
                "pipeline_type": "JSON-first with Google Sheets integration"
            }
            
            # Add error details if any occurred during saving
            if discovery_result.get("save_error"):
                summary_result["save_error"] = discovery_result["save_error"]
                summary_result["note"] = "Discovery succeeded but saving to Google Sheets encountered issues"
            
            # Include sample scholarship data for verification (first 2 scholarships)
            if scholarships:
                summary_result["sample_scholarships"] = scholarships[:2]
            
            self.logger.info(f"Daily discovery summary: {summary_result}")
            return summary_result
            
        except Exception as e:
            self.logger.error(f"Error in daily discovery: {e}")
            return {
                "success": False,
                "error": str(e),
                "scholarships_discovered": 0,
                "scholarships_saved": 0,
                "scholarships_skipped": 0,
                "timestamp": datetime.now().isoformat(),
                "duration_seconds": (datetime.now() - start_time).total_seconds() if 'start_time' in locals() else 0
            }
            search_criteria = f"new scholarships for college students {datetime.now().year} financial aid opportunities"
        
        try:
            # Discover scholarships
            discovery_result = await self.discover_scholarships(search_criteria)
            
            # Save scholarships (try API first, fallback to direct sheets)
            saved_scholarships = []
            try:
                # Try API method first
                saved_scholarships = await self.save_scholarships_via_api(
                    discovery_result['scholarships']
                )
            except Exception as api_error:
                self.logger.warning(f"API save failed, trying direct sheets: {api_error}")
                # Fallback to direct sheets method
                if self.sheets_integration:
                    saved_scholarships = self.save_scholarships_direct(
                        discovery_result['scholarships']
                    )
            
            summary = {
                'discovery_timestamp': discovery_result['discovery_timestamp'],
                'search_criteria': search_criteria,
                'scholarships_discovered': len(discovery_result['scholarships']),
                'scholarships_saved': len(saved_scholarships),
                'sources_count': len(discovery_result['sources']),
                'success': True
            }
            
            self.logger.info(f"Daily discovery completed: {summary}")
            return summary
            
        except Exception as e:
            self.logger.error(f"Daily discovery failed: {e}")
            return {
                'discovery_timestamp': datetime.now().isoformat(),
                'search_criteria': search_criteria,
                'error': str(e),
                'success': False
            }
    
    def _scholarship_data_to_dict(self, scholarship_data) -> Dict[str, Any]:
        """Convert ScholarshipData object to dictionary format."""
        return {
            "id": scholarship_data.id,
            "title": scholarship_data.title,
            "description": scholarship_data.description,
            "amount": scholarship_data.amount,
            "deadline": scholarship_data.deadline,
            "eligibility": scholarship_data.eligibility,
            "requirements": scholarship_data.requirements,
            "applicationUrl": scholarship_data.application_url,
            "provider": scholarship_data.provider,
            "category": scholarship_data.category,
            "status": scholarship_data.status,
            "createdDate": scholarship_data.created_date,
            "modifiedDate": scholarship_data.modified_date,
            "createdBy": scholarship_data.created_by,
            "lastModifiedBy": scholarship_data.last_modified_by
        }
    
    def validate_scholarship_completeness(self, scholarship: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate scholarship data completeness and return validation status with missing fields.
        
        Args:
            scholarship: Scholarship dictionary to validate
            
        Returns:
            Tuple of (is_valid, list_of_missing_critical_fields)
        """
        missing_fields = []
        
        # Critical fields that must be present and non-empty
        critical_fields = {
            'title': 'Title',
            'description': 'Description', 
            'amount': 'Amount',
            'deadline': 'Deadline',
            'provider': 'Provider'
        }
        
        for field, display_name in critical_fields.items():
            value = scholarship.get(field, '').strip()
            if not value or value.lower() in ['not available', 'n/a', 'not specified']:
                missing_fields.append(display_name)
        
        # Additional validation
        if scholarship.get('title') and len(scholarship['title']) < 5:
            missing_fields.append('Title (too short)')
        
        if scholarship.get('description') and len(scholarship['description']) < 20:
            missing_fields.append('Description (too short)')
        
        # URL validation
        application_url = scholarship.get('applicationUrl', '').strip()
        if not application_url or not (application_url.startswith('http://') or application_url.startswith('https://')):
            missing_fields.append('Valid Application URL')
        
        return len(missing_fields) == 0, missing_fields
    
    def generate_discovery_report(self, discovery_result: Dict[str, Any]) -> str:
        """Generate a human-readable report of the discovery process."""
        if not discovery_result.get("success", False):
            return f"❌ Discovery failed: {discovery_result.get('error', 'Unknown error')}"
        
        discovered = discovery_result.get("scholarships_discovered", 0)
        saved = discovery_result.get("scholarships_saved", 0)
        skipped = discovery_result.get("scholarships_skipped", 0)
        duration = discovery_result.get("duration_seconds", 0)
        
        report = f"""
📊 SCHOLARSHIP DISCOVERY REPORT
=================================
✅ Status: Successful
🔍 Search Criteria: {discovery_result.get('search_criteria', 'Default')}
📅 Timestamp: {discovery_result.get('timestamp', 'Unknown')}
⏱️  Duration: {duration:.1f} seconds

📈 RESULTS SUMMARY:
• Scholarships Discovered: {discovered}
• Scholarships Saved: {saved}
• Scholarships Skipped: {skipped}
• Success Rate: {(saved/discovered*100) if discovered > 0 else 0:.1f}%

🔗 Sources Processed: {discovery_result.get('sources_count', 0)}
🔧 Pipeline: {discovery_result.get('pipeline_type', 'Standard')}
"""
        
        if discovery_result.get("save_error"):
            report += f"\n⚠️  Save Warning: {discovery_result['save_error']}"
        
        if discovery_result.get("sample_scholarships"):
            report += "\n\n📋 SAMPLE SCHOLARSHIPS FOUND:"
            for i, scholarship in enumerate(discovery_result["sample_scholarships"][:2], 1):
                report += f"\n{i}. {scholarship.get('title', 'Unknown Title')}"
                report += f"\n   Provider: {scholarship.get('provider', 'Unknown')}"
                report += f"\n   Amount: {scholarship.get('amount', 'Unknown')}"
                report += f"\n   Deadline: {scholarship.get('deadline', 'Unknown')}"
        
        return report
