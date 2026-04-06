# Tech Company Web Crawler and Job Openings Tracker

A comprehensive system for tracking tech job openings in the Dallas-Fort Worth (DFW) area with AI-powered interview practice and skill gap analysis.

## 🚀 Features

### Core Features
- **Distributed Web Crawler**: Built with message queues (Redis) and worker pools
- **Respectful Rate Limiting**: Complies with robots.txt and implements smart rate limiting
- **Job Posting Extraction**: Automatically extracts job requirements, skills, and qualifications
- **Company Database**: Stores company info, HR contacts, and job listings
- **Real-time Updates**: Continuously updates with new job openings

### AI-Powered Features
- **NLP Job Requirement Extraction**: Automatically categorizes skills, experience levels, and qualifications
- **AI Interview Practice**: Speech-to-text interview simulation with real-time feedback
- **Skill Gap Analysis**: Compares your resume against job requirements
- **Keyword Analysis**: Analyzes interview responses for relevant keywords

### Analytics
- **Market Analytics**: Insights into tech job market trends
- **Skill Demand Tracking**: See which skills are in highest demand
- **Salary Trends**: Average salary by experience level and job type
- **Company Hiring Patterns**: Track company hiring activity

## 📁 Project Structure

```
D:\7\
├── requirements.txt          # Python dependencies
├── config.yaml               # Configuration file
├── database/
│   └── schema.sql            # MySQL database schema
├── crawler/
│   └── distributed_crawler.py  # Web crawler implementation
├── ai_modules/
│   ├── nlp_processor.py      # NLP for job extraction
│   └── interview_practice.py # AI interview system
├── backend/
│   ├── main.py               # FastAPI backend
│   └── database.py           # Database operations
├── frontend/
│   └── index.html            # Web UI
├── tests/                    # Unit tests
└── logs/                     # Application logs
```

## 🛠️ Installation

### Prerequisites
- Python 3.11+
- MySQL 8.0+
- Redis 7.0+
- Chrome browser (for Selenium)

### Setup

1. **Clone and navigate to the project**
```bash
cd D:\7
```

2. **Create virtual environment**
```bash
python -m venv venv
venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Setup database**
```bash
# Create MySQL database
mysql -u root -p < database/schema.sql

# Or import in MySQL Workbench/HeidiSQL
```

5. **Configure application**
```bash
# Edit config.yaml with your settings
# - Database credentials
# - Redis connection
# - API keys (OpenAI, etc.)
```

6. **Download NLP models**
```bash
python -m spacy download en_core_web_sm
```

## ⚙️ Configuration

Edit `config.yaml` to customize:

```yaml
database:
  host: "localhost"
  port: 3306
  username: "your_user"
  password: "your_password"
  name: "tech_jobs_db"

redis:
  host: "localhost"
  port: 6379

crawler:
  request_delay: 2.0
  max_concurrent: 5
```

## 🚀 Running the Application

### Start Backend API
```bash
cd D:\7\backend
python main.py
```
API will be available at http://localhost:8000

### Start Frontend
Open `D:\7\frontend\index.html` in a web browser

### Start Crawler
```bash
python -m crawler.distributed_crawler
```

## 📡 API Endpoints

### Jobs
- `GET /api/jobs` - Search jobs
- `POST /api/jobs` - Create job posting
- `GET /api/jobs/{id}` - Get job details
- `GET /api/jobs/{id}/similar` - Find similar jobs

### Companies
- `GET /api/companies` - List companies
- `GET /api/companies/{id}` - Get company details

### Interview
- `POST /api/interview/start` - Start interview session
- `POST /api/interview/{id}/respond` - Submit response
- `POST /api/interview/{id}/end` - End session

### Analytics
- `GET /api/analytics/overview` - Market overview
- `GET /api/analytics/skills-demand` - Skill demand
- `GET /api/analytics/salary-trends` - Salary data

## 🧪 Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=ai_modules tests/
```

## 🎯 Usage Examples

### Starting a Job Search
```python
import requests

response = requests.post(
    "http://localhost:8000/api/jobs",
    json={
        "city": "Dallas",
        "experience_level": "senior",
        "skills": ["Python", "AWS"]
    }
)
jobs = response.json()
```

### AI Interview Practice
```python
# Start interview for a specific job
response = requests.post(
    "http://localhost:8000/api/interview/start",
    json={"job_id": 123, "interview_type": "mixed"}
)
session = response.json()

# Submit your answer (transcribed from speech)
response = requests.post(
    f"http://localhost:8000/api/interview/{session['session_id']}/respond",
    json={"transcript": "Your answer text here..."}
)
feedback = response.json()
```

### Analyzing Resume Match
```python
# Upload resume
response = requests.post(
    "http://localhost:8000/api/resume/upload",
    json={"user_id": "user123", "filename": "resume.pdf", "file_content": "..."}
)
resume_id = response.json()["resume_id"]

# Compare against job requirements
response = requests.post(
    "http://localhost:8000/api/skill-gap/analyze",
    json={"resume_id": resume_id, "job_id": 456}
)
analysis = response.json()
```

## 🔒 Important Notes

### robots.txt Compliance
The crawler respects robots.txt and implements:
- Polite rate limiting (2+ seconds between requests)
- User-agent identification
- Request throttling

### Legal Considerations
- Only crawl publicly available job postings
- Respect terms of service of job boards
- Do not use LinkedIn crawling without proper authorization
- Check `config.yaml` for LinkedIn settings (disabled by default)

### Rate Limiting
Default settings:
- 0.5 requests/second for company pages
- 0.3 requests/second for job boards
- Automatic backoff on 429 responses

## 📈 Architecture

```
                    ┌─────────────────┐
                    │   Frontend UI   │
                    │  (index.html)   │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  FastAPI Server  │
                    │   (Port 8000)    │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
┌───────▼───────┐   ┌───────▼───────┐   ┌───────▼───────┐
│   MySQL DB    │   │  Redis Queue  │   │  Celery Tasks  │
│  (Jobs/Companies)│ │(Crawler Tasks)│ │  (Background)  │
└───────────────┘   └───────────────┘   └───────────────┘
```

## 🛠️ Technologies Used

- **Backend**: FastAPI, SQLAlchemy, MySQL
- **Crawler**: aiohttp, BeautifulSoup, Selenium
- **Queue**: Redis, Celery
- **NLP**: spaCy, NLTK, scikit-learn
- **AI**: OpenAI API (optional for enhanced features)
- **Frontend**: HTML5, CSS3, Vanilla JavaScript

## 📝 License

This project is for educational purposes. Please ensure compliance with all applicable laws and terms of service when using web crawlers.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📞 Support

For issues and questions:
- Open a GitHub issue
- Check the logs in `D:\7\logs\`

---

Built with ❤️ for the DFW tech community
