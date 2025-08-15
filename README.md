# AI Scholarship Discovery Agent

An intelligent, AI-powered scholarship discovery platform that combines a LangGraph-based agent with a modern React frontend to automatically find, extract, and organize scholarship opportunities from across the web.

##  Overview

This project features an advanced AI agent built with LangGraph that intelligently searches the web for scholarship opportunities, extracts structured data, and provides a clean interface for students to discover relevant scholarships. The agent uses Google's Gemini 2.0 Flash model to understand scholarship requirements, categorize opportunities, and ensure data quality.

##  Architecture

- **AI Agent**: LangGraph-powered scholarship discovery agent using Gemini 2.0 Flash
- **Backend**: FastAPI application with agent orchestration and Google Sheets integration
- **Frontend**: React + TypeScript web application with real-time agent communication
- **Data Pipeline**: JSON-first structured extraction with automatic validation and enhancement
- **Integration**: Direct Google Sheets API integration with audit logging

##  Features

### AI Agent Capabilities
- **Intelligent Query Generation**: Automatically generates optimized search queries based on user criteria
- **Web Research**: Uses Google Search API with Gemini 2.0 Flash to find scholarship opportunities
- **Structured Data Extraction**: Converts unstructured web content into standardized JSON format
- **Smart Enhancement**: AI-powered categorization and missing field inference
- **Quality Validation**: Multi-stage filtering to ensure only high-quality scholarships are saved
- **Deduplication**: Prevents duplicate scholarship entries across discovery sessions
- **URL Validation**: Fallback search for missing application URLs

### Web Application
- **Real-time Agent Interaction**: Stream live updates from the AI agent during discovery
- **Activity Timeline**: Visual representation of agent's research process
- **Chat Interface**: Natural language interaction with the scholarship agent
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile devices
- **Modern UI**: Clean, shadcn/ui-based interface with TypeScript safety

### Data Management
- **JSON-First Pipeline**: Structured data extraction with 15-field schema matching Google Sheets
- **Google Sheets Integration**: Direct API integration for data storage and retrieval
- **Automatic Metadata**: Auto-generated IDs, timestamps, and audit trails
- **Data Quality Metrics**: Comprehensive validation and quality reporting
- **Audit Logging**: Complete tracking of agent activities and data changes

##  Tech Stack

### AI Agent & Backend
- **LangGraph** for agent orchestration and workflow management
- **Google Gemini 2.0 Flash** for natural language understanding and reasoning
- **FastAPI** for high-performance API server
- **Google Search API** for web research capabilities
- **Pydantic** for data validation and schema enforcement
- **Google Sheets API** for direct spreadsheet integration

### Frontend
- **React 18** + TypeScript for the user interface
- **shadcn/ui** + Tailwind CSS for modern UI components
- **Vite** for fast development and building
- **LangChain SDK** for real-time agent communication
- **Streaming API** for live updates during agent execution

### Data & Infrastructure
- **JSON-first Pipeline** with structured data extraction
- **Google Sheets** as primary data store
- **UUID Generation** for unique scholarship identification
- **ISO Timestamp Management** for audit trails
- **Environment-based Configuration** for flexible deployment

##  Prerequisites

- **Node.js 18+** and npm (for frontend)
- **Python 3.9+** (for AI agent backend)
- **Google API Key** (for Gemini 2.0 Flash model)
- **Google Search API** credentials (for web research)
- **Google Sheets API** credentials (for data storage)
- Optional: **Docker** and **Docker Compose** for containerized deployment

##  Quick Start

### Option 1: Docker Compose (Recommended)

1. **Clone and configure**:
   ```bash
   git clone <repository-url>
   cd ai-scholarship-agent
   cp .env.example .env
   # Edit .env with your API keys
   ```

2. **Start with Docker Compose**:
   ```bash
   docker-compose up -d
   ```

3. **Access the application**:
   - Frontend: `http://localhost:3000`
   - Backend API: `http://localhost:8123`

### Option 2: Manual Setup

1. **Backend Setup**:
   ```bash
   cd backend
   pip install -r requirements.txt
   # Configure environment variables
   export GEMINI_API_KEY="your-gemini-api-key"
   export GOOGLE_SEARCH_API_KEY="your-search-api-key"
   # Start the agent server
   python -m langgraph up
   ```

2. **Frontend Setup**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. **Open your browser** to `http://localhost:5173`

##  How the AI Agent Works

### Discovery Process

1. **Query Understanding**: The agent analyzes your scholarship search criteria
2. **Search Strategy**: Generates multiple optimized search queries for comprehensive coverage
3. **Web Research**: Executes searches using Google Search API and analyzes results
4. **Content Extraction**: Uses Gemini 2.0 Flash to extract structured scholarship data
5. **Enhancement**: Fills missing fields, categorizes scholarships, and validates URLs
6. **Quality Control**: Filters out low-quality entries and removes duplicates
7. **Storage**: Saves validated scholarships directly to Google Sheets with full audit trails

### Data Schema

Each scholarship follows this standardized format:
```json
{
  "id": "uuid",
  "title": "Scholarship Name",
  "description": "Detailed description",
  "amount": "$5,000",
  "deadline": "2025-07-15",
  "eligibility": "Requirements list",
  "requirements": "Application requirements",
  "application_url": "https://...",
  "provider": "Organization name",
  "category": "STEM/Arts/General/etc",
  "status": "Active",
  "created_date": "ISO timestamp",
  "modified_date": "ISO timestamp",
  "created_by": "AI Agent",
  "last_modified_by": "AI Agent"
}
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the backend directory:

```bash
# AI Model Configuration
GEMINI_API_KEY=your_gemini_api_key_here
GOOGLE_SEARCH_API_KEY=your_google_search_api_key
GOOGLE_SEARCH_ENGINE_ID=your_custom_search_engine_id

# Google Sheets Integration
GOOGLE_SHEETS_CREDENTIALS_PATH=path/to/service-account.json
SCHOLARSHIP_SPREADSHEET_ID=your_spreadsheet_id

# Agent Configuration
AGENT_AUTH_TOKEN=optional_auth_token
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_api_key
```

### Google APIs Setup

1. **Google AI Studio**: Get your Gemini API key from [aistudio.google.com](https://aistudio.google.com)
2. **Google Search API**: Enable Custom Search API in Google Cloud Console
3. **Google Sheets API**: Create a service account and download credentials JSON

##  Usage Examples

### Interactive Chat
```
User: "Find STEM scholarships for undergraduate students"
Agent: Generates search queries → Researches web → Extracts data → Saves to sheets
```

### Specific Criteria
```
User: "Find scholarships for computer science majors with deadlines after July 2025"
Agent: Tailored search → Quality filtering → Structured extraction
```

### Bulk Discovery
```
User: "Discover all available scholarships for minority students in engineering"
Agent: Comprehensive search → Multi-source research → Deduplication → Bulk save
```

##  Monitoring & Analytics

- **Real-time Progress**: Watch the agent work through the discovery pipeline
- **Quality Metrics**: Track data quality scores and validation results
- **Performance Stats**: Monitor search success rates and processing times
- **Audit Logs**: Complete history of agent activities and data changes

##  Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

##  License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

##  Acknowledgments

- **LangGraph** for the agent framework
- **Google Gemini** for AI capabilities
- **shadcn/ui** for the beautiful UI components
- **The open-source community** for the amazing tools and libraries
