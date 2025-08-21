# Insurance Document Analyzer

A FastAPI-based intelligent insurance document analyzer that helps users understand their insurance coverage by analyzing policy documents and answering specific coverage questions.

## 🎯 Overview

The Insurance Document Analyzer is a sophisticated API service that leverages OpenAI's GPT-4o-mini model to analyze insurance policy documents and provide accurate, professional coverage assessments. Upload your Policy Disclosure Statement (PDS) and Schedule of Coverage PDFs along with your specific question to receive immediate, structured analysis.

## ✨ Features

- **Single API Call Analysis**: Upload both PDS and Schedule PDFs with your question for complete analysis
- **AI-Powered Assessment**: Fine-tuned model with conservative assessment framework
- **Structured Responses**: Professional 40-word explanations with percentage-based confidence scoring
- **Multiple Insurance Types**: Supports auto, home, health, construction, and other insurance types
- **Professional Interpretation**: Expert-level insurance policy interpretation
- **Modular Architecture**: Clean, maintainable FastAPI-based modular design
- **Health Monitoring**: Comprehensive health check endpoints
- **PDF Processing**: Robust PDF text extraction and processing

## 🏗️ Architecture

The application follows a modular FastAPI architecture:

```
app/
├── api/v1/
│   └── endpoints/
│       ├── coverage.py    # Main analysis endpoints
│       └── health.py      # Health check endpoints
├── core/
│   └── config.py          # Application configuration
├── schemas/
│   └── coverage.py        # Pydantic models
├── services/
│   ├── insurance_analyzer.py  # AI analysis service
│   └── pdf_extractor.py       # PDF processing service
├── utils/
│   ├── validators.py      # Input validation
│   └── text_processor.py # Text processing utilities
└── main.py               # Application entry point
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- OpenAI API key

### Installation

1. Clone the repository:
```bash
git clone https://github.com/Tanjeelur/insurance_chatbot.git
cd insurance_chatbot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
echo "OPENAI_API_KEY=your_openai_api_key_here" > .env
```

### Running the Application

```bash
# Run with uvicorn directly
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# Or run the main.py file
python app/main.py
```

The API will be available at `http://localhost:8000`

## 📚 API Documentation

### Interactive Documentation

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Main Endpoints

#### Analyze Coverage
**POST** `/api/v1/analyze-coverage`

Upload insurance documents and get immediate coverage analysis.

**Parameters:**
- `policy_disclosure` (file): Policy Disclosure Statement PDF
- `schedule_coverage` (file): Schedule of Coverage PDF  
- `insurance_type` (string): Type of insurance (e.g., auto, home, health, construction)
- `question` (string): Your specific coverage question

**Response:**
```json
{
  "percentage_score": 65,
  "likelihood_ranking": "Somewhat Likely",
  "explanation": "Coverage appears applicable under storm damage provisions, subject to deductible requirements and specific policy conditions outlined in the schedule documentation."
}
```

#### Health Check
**GET** `/api/v1/health`

Basic health check endpoint.

**GET** `/api/v1/health/detailed`

Detailed health check including OpenAI connectivity and service status.

## 🔧 Configuration

The application uses environment variables for configuration:

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key (required) | - |
| `PROJECT_NAME` | Application name | "Insurance Document Analyzer" |
| `PROJECT_VERSION` | Application version | "2.0.0" |
| `OPENAI_MODEL` | OpenAI model to use | "gpt-4o-mini" |
| `TEMPERATURE` | Model temperature | 0.1 |
| `MAX_TOKENS` | Maximum tokens per response | 1000 |

## 💻 Usage Examples

### Using cURL

```bash
# Analyze coverage
curl -X POST "http://localhost:8000/api/v1/analyze-coverage" \
  -F "policy_disclosure=@path/to/policy.pdf" \
  -F "schedule_coverage=@path/to/schedule.pdf" \
  -F "insurance_type=auto" \
  -F "question=Is collision damage covered under this policy?"

# Health check
curl -X GET "http://localhost:8000/api/v1/health"
```

### Using Python

```python
import requests

# Analyze coverage
with open('policy.pdf', 'rb') as policy_file, \
     open('schedule.pdf', 'rb') as schedule_file:
    
    response = requests.post(
        'http://localhost:8000/api/v1/analyze-coverage',
        files={
            'policy_disclosure': policy_file,
            'schedule_coverage': schedule_file
        },
        data={
            'insurance_type': 'auto',
            'question': 'Is collision damage covered under this policy?'
        }
    )
    
    result = response.json()
    print(f"Coverage likelihood: {result['percentage_score']}%")
    print(f"Ranking: {result['likelihood_ranking']}")
    print(f"Explanation: {result['explanation']}")
```

## 📋 Response Format

The analyzer provides structured responses with:

- **percentage_score** (integer): Confidence score from 0-100
- **likelihood_ranking** (string): Human-readable likelihood assessment
  - "Highly Unlikely" (0-20%)
  - "Unlikely" (21-50%)
  - "Somewhat Likely" (51-65%)
  - "Likely" (66-80%)
  - "Highly Likely" (81-100%)
- **explanation** (string): Professional 40-word explanation

## 🔒 Security & Validation

- PDF file type validation
- Input sanitization and validation
- Error handling for malformed requests
- Secure file processing
- API rate limiting ready architecture

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support, please open an issue in the GitHub repository or contact the maintainers.

## 🔄 Version History

- **v2.0.0** - Current version with modular FastAPI architecture
- Fine-tuned model integration
- Comprehensive coverage analysis
- Professional response formatting 
