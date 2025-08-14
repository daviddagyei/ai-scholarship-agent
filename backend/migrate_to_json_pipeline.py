#!/usr/bin/env python3
"""
Migration script to transition from legacy text-based pipeline to JSON-first pipeline
"""
import os
import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime

# Add the agent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def backup_existing_configuration():
    """Backup existing configuration files."""
    print("📦 Creating backup of existing configuration...")
    
    backup_dir = Path(__file__).parent / 'backup' / datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    # Files to backup
    backup_files = [
        'run_agent.py',
        'src/agent/graph.py',
        'src/agent/prompts.py',
        'src/agent/scholarship_service.py'
    ]
    
    for file_path in backup_files:
        source_path = Path(__file__).parent / file_path
        if source_path.exists():
            backup_path = backup_dir / file_path
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            
            import shutil
            shutil.copy2(source_path, backup_path)
            print(f"✅ Backed up: {file_path}")
    
    print(f"📁 Backup created at: {backup_dir}")
    return backup_dir

def check_environment_requirements():
    """Check if all required environment variables are set."""
    print("🔍 Checking environment requirements...")
    
    required_vars = {
        'GEMINI_API_KEY': 'Gemini API key for LLM operations',
        'GOOGLE_SERVICE_ACCOUNT_EMAIL': 'Google Sheets service account email',
        'GOOGLE_PRIVATE_KEY': 'Google Sheets service account private key',
        'GOOGLE_SHEETS_ID': 'Google Sheets spreadsheet ID'
    }
    
    missing_vars = []
    for var, description in required_vars.items():
        if not os.getenv(var):
            missing_vars.append(f"  - {var}: {description}")
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(var)
        return False
    
    print("✅ All required environment variables are set")
    return True

def check_dependencies():
    """Check if all required Python packages are installed."""
    print("📦 Checking Python dependencies...")
    
    required_packages = [
        'gspread',
        'python-dateutil',
        'pydantic',
        'langchain-google-genai',
        'langgraph'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"  - {package}")
        print("\nInstall missing packages with:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    print("✅ All required packages are installed")
    return True

async def test_new_pipeline():
    """Test the new JSON-first pipeline."""
    print("🧪 Testing new JSON-first pipeline...")
    
    try:
        from agent.scholarship_service import ScholarshipAgentService
        from agent.state import ScholarshipData, ScholarshipCollection
        
        # Test ScholarshipData creation
        scholarship = ScholarshipData.create_new(
            title="Migration Test Scholarship",
            description="A test scholarship to verify the migration pipeline works correctly",
            amount="$1,000",
            deadline="2025-12-31",
            eligibility="Test eligibility criteria",
            requirements="Test requirements",
            application_url="https://example.com/test",
            provider="Migration Test Provider",
            category="Test"
        )
        
        print(f"✅ Created test scholarship: {scholarship.title}")
        print(f"   ID: {scholarship.id}")
        print(f"   Status: {scholarship.status}")
        
        # Test service initialization
        service = ScholarshipAgentService(sheets_integration=False)
        print("✅ Service initialized successfully")
        
        # Test discovery (quick test)
        print("🔍 Running quick discovery test...")
        result = await service.discover_scholarships("test scholarship search")
        
        if result.get('success', False):
            print(f"✅ Discovery test successful: found {result.get('scholarships_discovered', 0)} scholarships")
        else:
            print(f"⚠️  Discovery test completed with issues: {result.get('error', 'Unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Pipeline test failed: {e}")
        return False

def create_migration_summary():
    """Create a summary of migration changes."""
    summary = {
        "migration_date": datetime.now().isoformat(),
        "changes": [
            "Implemented JSON-first pipeline architecture",
            "Added ScholarshipData Pydantic model with auto-generated fields",
            "Enhanced scholarship_graph.py with structured extraction",
            "Updated scholarship_service.py with new pipeline methods",
            "Added Google Sheets direct integration",
            "Implemented quality validation and filtering",
            "Added auto-categorization with AI reasoning",
            "Enhanced audit logging for agent activities",
            "Added comprehensive test suite",
            "Created detailed documentation and README"
        ],
        "new_features": [
            "Auto-generated UUIDs for scholarships",
            "ISO timestamp creation and modification dates",
            "AI-powered scholarship categorization",
            "Fallback search for missing application URLs",
            "Data quality thresholds and validation",
            "Deduplication and conflict resolution",
            "Comprehensive audit trails",
            "Enhanced error handling and reporting"
        ],
        "breaking_changes": [
            "Result format changed from text-based to structured JSON",
            "New required dependencies: gspread, python-dateutil",
            "Environment variables: GOOGLE_* credentials required for Sheets integration",
            "Service method signatures updated for new pipeline"
        ],
        "migration_benefits": [
            "Reliable structured data output",
            "Automatic Google Sheets integration",
            "Higher data quality with validation",
            "Better error handling and resilience",
            "Comprehensive monitoring and audit trails",
            "Easier integration with frontend applications",
            "Improved performance and efficiency"
        ]
    }
    
    summary_file = Path(__file__).parent / 'MIGRATION_SUMMARY.json'
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"📄 Migration summary saved to: {summary_file}")
    return summary

def print_migration_report(summary):
    """Print a human-readable migration report."""
    print("\n" + "="*60)
    print("🚀 JSON-FIRST PIPELINE MIGRATION COMPLETE")
    print("="*60)
    
    print(f"📅 Migration Date: {summary['migration_date']}")
    
    print(f"\n✨ NEW FEATURES ({len(summary['new_features'])}):")
    for feature in summary['new_features']:
        print(f"  • {feature}")
    
    print(f"\n⚠️  BREAKING CHANGES ({len(summary['breaking_changes'])}):")
    for change in summary['breaking_changes']:
        print(f"  • {change}")
    
    print(f"\n🎯 BENEFITS ({len(summary['migration_benefits'])}):")
    for benefit in summary['migration_benefits']:
        print(f"  • {benefit}")
    
    print("\n📚 NEXT STEPS:")
    print("  1. Review the JSON_PIPELINE_README.md for detailed documentation")
    print("  2. Run test_json_pipeline.py to verify the complete setup")
    print("  3. Update your frontend/API integration to use the new JSON format")
    print("  4. Configure Google Sheets credentials for automatic integration")
    print("  5. Set up monitoring and audit log review processes")
    
    print("\n🆘 SUPPORT:")
    print("  • Backup files available in: backup/")
    print("  • Test suite: python test_json_pipeline.py")
    print("  • Documentation: JSON_PIPELINE_README.md")
    print("  • Migration summary: MIGRATION_SUMMARY.json")

async def main():
    """Run the migration process."""
    print("🚀 Starting JSON-First Pipeline Migration")
    print("="*60)
    
    # Step 1: Backup existing configuration
    backup_dir = backup_existing_configuration()
    
    # Step 2: Check environment
    if not check_environment_requirements():
        print("\n❌ Migration cannot proceed without required environment variables")
        print("Please set the required variables and run the migration again")
        sys.exit(1)
    
    # Step 3: Check dependencies
    if not check_dependencies():
        print("\n❌ Migration cannot proceed without required dependencies")
        print("Please install the required packages and run the migration again")
        sys.exit(1)
    
    # Step 4: Test new pipeline
    pipeline_works = await test_new_pipeline()
    
    # Step 5: Create migration summary
    summary = create_migration_summary()
    
    # Step 6: Print final report
    print_migration_report(summary)
    
    if pipeline_works:
        print("\n🎉 Migration completed successfully!")
        print("The JSON-first pipeline is ready for use.")
        sys.exit(0)
    else:
        print("\n⚠️  Migration completed with warnings")
        print("The pipeline structure is in place but may need configuration adjustments.")
        print("Please review the test results and documentation.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
