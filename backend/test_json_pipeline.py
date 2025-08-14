#!/usr/bin/env python3
"""
Test script for the enhanced JSON-first scholarship discovery pipeline
"""
import os
import sys
import asyncio
import json
from pathlib import Path

# Add the agent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from agent.scholarship_service import ScholarshipAgentService
from agent.state import ScholarshipData, ScholarshipCollection
from dotenv import load_dotenv

def setup_test_environment():
    """Setup test environment with necessary paths."""
    # Load environment variables
    load_dotenv(Path(__file__).parent.parent.parent / '.env')
    load_dotenv(Path(__file__).parent.parent / '.env')
    
    # Validate required environment variables
    required_vars = ["GEMINI_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {missing_vars}")
        return False
    
    print("✅ Environment setup complete")
    return True

def test_scholarship_data_creation():
    """Test creating ScholarshipData objects."""
    print("\n🧪 Testing ScholarshipData creation...")
    
    try:
        scholarship = ScholarshipData.create_new(
            title="Test Scholarship for STEM Students",
            description="A comprehensive scholarship program for undergraduate students pursuing STEM degrees with a focus on underrepresented minorities.",
            amount="$5,000",
            deadline="2025-12-31",
            eligibility="Undergraduate students, 3.0 GPA minimum, STEM majors, US citizens or permanent residents",
            requirements="Application form, Essay (500 words), Transcript, Two letters of recommendation",
            application_url="https://example.com/apply/stem-scholarship",
            provider="STEM Education Foundation",
            category="STEM"
        )
        
        print(f"✅ Created scholarship: {scholarship.title}")
        print(f"   ID: {scholarship.id}")
        print(f"   Status: {scholarship.status}")
        print(f"   Created: {scholarship.created_date}")
        
        # Test collection
        collection = ScholarshipCollection()
        collection.add_scholarship(scholarship)
        
        print(f"✅ Added to collection. Total scholarships: {len(collection.scholarships)}")
        
        # Test Google Sheets format
        sheets_data = collection.to_google_sheets_format()
        print(f"✅ Generated Google Sheets format with {len(sheets_data)} rows")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in ScholarshipData test: {e}")
        return False

async def test_discovery_pipeline():
    """Test the complete discovery pipeline."""
    print("\n🧪 Testing discovery pipeline...")
    
    try:
        # Initialize service
        service = ScholarshipAgentService(
            backend_api_url="http://localhost:5001",
            sheets_integration=False  # Don't save to sheets in test
        )
        
        # Test search criteria
        test_criteria = "STEM scholarships for undergraduate students 2025"
        
        print(f"🔍 Running discovery with criteria: {test_criteria}")
        
        # Run discovery
        result = await service.discover_scholarships(test_criteria)
        
        print(f"📊 Discovery result keys: {list(result.keys())}")
        print(f"✅ Success: {result.get('success', False)}")
        print(f"🔍 Scholarships discovered: {result.get('scholarships_discovered', 0)}")
        
        if result.get('scholarships'):
            print(f"📋 First scholarship title: {result['scholarships'][0].get('title', 'Unknown')}")
        
        # Validate data quality
        if result.get('scholarships'):
            quality_report = validate_scholarship_quality(result['scholarships'])
            print(f"📊 Quality report: {quality_report}")
        
        return result.get('success', False)
        
    except Exception as e:
        print(f"❌ Error in discovery pipeline test: {e}")
        return False

def validate_scholarship_quality(scholarships):
    """Validate the quality of discovered scholarships."""
    quality_counts = {"high_quality": 0, "medium_quality": 0, "low_quality": 0}
    
    for scholarship in scholarships:
        required_fields = ['title', 'description', 'amount', 'deadline', 'provider', 'applicationUrl']
        present_fields = sum(1 for field in required_fields 
                           if scholarship.get(field) and scholarship[field] != 'Not available')
        
        if present_fields >= 5:
            quality_counts["high_quality"] += 1
        elif present_fields >= 3:
            quality_counts["medium_quality"] += 1
        else:
            quality_counts["low_quality"] += 1
    
    return quality_counts

async def test_daily_discovery():
    """Test the daily discovery process."""
    print("\n🧪 Testing daily discovery process...")
    
    try:
        service = ScholarshipAgentService(
            sheets_integration=False  # Don't save to sheets in test
        )
        
        # Run daily discovery
        result = await service.run_daily_discovery("scholarships for college students 2025")
        
        print(f"📊 Daily discovery result:")
        print(f"   Success: {result.get('success', False)}")
        print(f"   Discovered: {result.get('scholarships_discovered', 0)}")
        print(f"   Saved: {result.get('scholarships_saved', 0)}")
        print(f"   Skipped: {result.get('scholarships_skipped', 0)}")
        print(f"   Duration: {result.get('duration_seconds', 0):.1f}s")
        
        return result.get('success', False)
        
    except Exception as e:
        print(f"❌ Error in daily discovery test: {e}")
        return False

def test_json_schema_validation():
    """Test JSON schema validation and formatting."""
    print("\n🧪 Testing JSON schema validation...")
    
    try:
        # Test sample data
        sample_scholarship = {
            "title": "Innovation in Technology Scholarship",
            "description": "Supporting the next generation of technology innovators",
            "amount": "$2,500",
            "deadline": "2025-06-30",
            "eligibility": "Computer Science or Engineering majors, 3.5 GPA minimum",
            "requirements": "Application, Essay, Portfolio",
            "application_url": "https://tech-foundation.org/apply",
            "provider": "Technology Innovation Foundation",
            "category": "STEM"
        }
        
        # Create ScholarshipData object
        scholarship_data = ScholarshipData.create_new(**sample_scholarship)
        
        print(f"✅ Created scholarship with ID: {scholarship_data.id}")
        
        # Test validation function from service
        service = ScholarshipAgentService()
        
        # Convert to dict format for validation
        scholarship_dict = {
            "title": scholarship_data.title,
            "description": scholarship_data.description,
            "amount": scholarship_data.amount,
            "deadline": scholarship_data.deadline,
            "eligibility": scholarship_data.eligibility,
            "requirements": scholarship_data.requirements,
            "applicationUrl": scholarship_data.application_url,
            "provider": scholarship_data.provider,
            "category": scholarship_data.category
        }
        
        is_valid, missing_fields = service.validate_scholarship_completeness(scholarship_dict)
        
        print(f"✅ Validation result: {'Valid' if is_valid else 'Invalid'}")
        if missing_fields:
            print(f"   Missing fields: {missing_fields}")
        
        return is_valid
        
    except Exception as e:
        print(f"❌ Error in JSON schema validation test: {e}")
        return False

async def main():
    """Run all tests."""
    print("🚀 Starting JSON-First Scholarship Pipeline Tests")
    print("=" * 60)
    
    # Setup environment
    if not setup_test_environment():
        print("❌ Environment setup failed")
        sys.exit(1)
    
    # Run tests
    tests = [
        ("ScholarshipData Creation", test_scholarship_data_creation),
        ("JSON Schema Validation", test_json_schema_validation),
        ("Discovery Pipeline", test_discovery_pipeline),
        ("Daily Discovery", test_daily_discovery),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"Running: {test_name}")
        print('='*60)
        
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            
            results[test_name] = result
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"\n{status}: {test_name}")
            
        except Exception as e:
            print(f"💥 ERROR in {test_name}: {e}")
            results[test_name] = False
    
    # Summary
    print(f"\n{'='*60}")
    print("🏁 TEST SUMMARY")
    print('='*60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! The JSON-first pipeline is ready.")
        sys.exit(0)
    else:
        print(f"\n⚠️  {total - passed} tests failed. Please review the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
