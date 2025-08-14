#!/usr/bin/env python3
"""
Scholarship Agent Runner
Script for running the scholarship discovery agent on a schedule
"""
import os
import sys
import asyncio
import json
import argparse
from datetime import datetime
from pathlib import Path

# Add the agent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from agent.scholarship_service import ScholarshipAgentService


def setup_environment():
    """Load environment variables from the parent backend directory."""
    # Load from the main backend .env file
    # Corrected path to point to backend/.env
    backend_env_path = Path(__file__).parent.parent.parent / '.env'
    
    if backend_env_path.exists():
        from dotenv import load_dotenv
        load_dotenv(backend_env_path)
        print(f"Loaded environment from: {backend_env_path}")
    else:
        print(f"Warning: Backend .env file not found at {backend_env_path}")
    
    # Also load from the local .env file
    local_env_path = Path(__file__).parent.parent / '.env'
    if local_env_path.exists():
        from dotenv import load_dotenv
        load_dotenv(local_env_path)
        print(f"Loaded LangGraph environment from: {local_env_path}")
    else:
        print(f"Warning: LangGraph .env file not found at {local_env_path}")


async def run_discovery(search_criteria: str, output_file: str = None, 
                       save_to_sheets: bool = True) -> dict:
    """
    Run scholarship discovery with specified criteria using the enhanced JSON-first pipeline.
    
    Args:
        search_criteria: The search criteria for scholarships
        output_file: Optional file to save results to
        save_to_sheets: Whether to save results to Google Sheets
    
    Returns:
        Discovery results
    """
    print(f"🚀 Starting enhanced scholarship discovery")
    print(f"📋 Search criteria: {search_criteria}")
    print(f"⏰ Timestamp: {datetime.now().isoformat()}")
    print(f"💾 Save to sheets: {'Yes' if save_to_sheets else 'No'}")
    
    # Initialize the service
    service = ScholarshipAgentService(
        backend_api_url=os.getenv("BACKEND_API_URL", "http://localhost:5001"),
        sheets_integration=save_to_sheets
    )
    
    try:
        start_time = datetime.now()
        
        # Run the discovery using the new JSON-first pipeline
        if save_to_sheets:
            print("🔄 Running daily discovery with Google Sheets integration...")
            result = await service.run_daily_discovery(search_criteria)
        else:
            print("🔄 Running discovery without saving to sheets...")
            result = await service.discover_scholarships(search_criteria)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Save to file if specified
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"💾 Results saved to: {output_file}")
        
        # Generate and print comprehensive report
        if hasattr(service, 'generate_discovery_report'):
            report = service.generate_discovery_report(result)
            print(report)
        else:
            # Fallback simple summary
            print("\n" + "="*50)
            print("📊 DISCOVERY SUMMARY")
            print("="*50)
            print(f"✅ Success: {result.get('success', False)}")
            if 'scholarships_discovered' in result:
                print(f"🔍 Scholarships discovered: {result['scholarships_discovered']}")
                print(f"💾 Scholarships saved: {result.get('scholarships_saved', 0)}")
                print(f"⏭️  Scholarships skipped: {result.get('scholarships_skipped', 0)}")
            elif 'scholarships' in result:
                print(f"🔍 Scholarships discovered: {len(result['scholarships'])}")
            
            if result.get('error'):
                print(f"❌ Error: {result['error']}")
            
            print(f"⏱️  Duration: {duration:.1f} seconds")
        
        # Validate data quality
        if result.get('scholarships'):
            quality_report = validate_discovery_quality(result['scholarships'])
            print(f"\n📊 DATA QUALITY REPORT:")
            print(f"   High quality scholarships: {quality_report['high_quality']}")
            print(f"   Medium quality scholarships: {quality_report['medium_quality']}")
            print(f"   Low quality scholarships: {quality_report['low_quality']}")
        
        return result
        
    except Exception as e:
        print(f"💥 Error during discovery: {e}")
        return {"error": str(e), "success": False}


def validate_discovery_quality(scholarships: list) -> dict:
    """Validate the quality of discovered scholarships."""
    quality_counts = {"high_quality": 0, "medium_quality": 0, "low_quality": 0}
    
    for scholarship in scholarships:
        # Count required fields present
        required_fields = ['title', 'description', 'amount', 'deadline', 'provider', 'applicationUrl']
        present_fields = sum(1 for field in required_fields if scholarship.get(field) and scholarship[field] != 'Not available')
        
        if present_fields >= 5:
            quality_counts["high_quality"] += 1
        elif present_fields >= 3:
            quality_counts["medium_quality"] += 1
        else:
            quality_counts["low_quality"] += 1
    
    return quality_counts


def create_default_search_criteria() -> str:
    """Create default search criteria for current year focused on US scholarships."""
    current_year = datetime.now().year
    return f"new US scholarships and financial aid opportunities for American college students and students attending US universities {current_year}"


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Run scholarship discovery agent")
    parser.add_argument(
        "--search", 
        type=str, 
        help="Search criteria for scholarships",
        default=None
    )
    parser.add_argument(
        "--output", 
        type=str, 
        help="Output file for results (JSON)",
        default=None
    )
    parser.add_argument(
        "--no-sheets", 
        action="store_true", 
        help="Don't save to Google Sheets"
    )
    parser.add_argument(
        "--daily", 
        action="store_true", 
        help="Run daily discovery mode"
    )
    parser.add_argument(
        "--test", 
        action="store_true", 
        help="Run test mode (no saving)"
    )
    
    args = parser.parse_args()
    
    # Setup environment
    setup_environment()
    
    # Validate API key
    if not os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY") == "your_gemini_api_key_here":
        print("Error: GEMINI_API_KEY not properly configured")
        print("Please set your Gemini API key in the .env file")
        sys.exit(1)
    
    # Determine search criteria
    search_criteria = args.search or create_default_search_criteria()
    
    # Determine output file
    output_file = args.output
    if args.daily and not output_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"scholarship_discovery_{timestamp}.json"
    
    # Run discovery
    save_to_sheets = not args.no_sheets and not args.test
    
    try:
        result = asyncio.run(run_discovery(
            search_criteria=search_criteria,
            output_file=output_file,
            save_to_sheets=save_to_sheets
        ))
        
        if result.get("success", False):
            print("\n✅ Scholarship discovery completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ Scholarship discovery failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  Discovery interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
