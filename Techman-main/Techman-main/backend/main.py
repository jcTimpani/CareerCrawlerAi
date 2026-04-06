"""
Tech Jobs Crawler - FastAPI Backend
REST API for job tracking, interviews, and analytics
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Query, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
import uvicorn
import logging
import yaml
import sys
import os

# Add parent directory to path for ai_modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_modules.interview_practice import InterviewPracticeSystem, InterviewQuestion
import time
import uuid

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load configuration
import os
config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.yaml')
with open(config_path, 'r') as f:
    app_config = yaml.safe_load(f)

# Pydantic models
class CompanyCreate(BaseModel):
    name: str
    website: Optional[str] = None
    industry: Optional[str] = None
    size: Optional[str] = None
    location_city: Optional[str] = None
    location_state: Optional[str] = None
    phone: Optional[str] = None
    hr_email: Optional[str] = None
    linkedin_url: Optional[str] = None


class CompanyResponse(BaseModel):
    id: int
    name: str
    website: Optional[str] = None
    industry: Optional[str] = None
    location_city: Optional[str] = None
    location_state: Optional[str] = None
    phone: Optional[str] = None
    hr_email: Optional[str] = None
    linkedin_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class JobCreate(BaseModel):
    company_id: int
    title: str
    department: Optional[str] = None
    location_city: Optional[str] = None
    location_state: Optional[str] = None
    job_type: Optional[str] = "full-time"
    experience_level: Optional[str] = None
    description: Optional[str] = None
    application_url: Optional[str] = None
    posted_date: Optional[datetime] = None


class JobResponse(BaseModel):
    id: int
    title: str
    company_name: str
    location_city: Optional[str]
    experience_level: Optional[str]
    posted_date: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class JobSearch(BaseModel):
    keywords: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = "TX"
    experience_level: Optional[str] = None
    skills: Optional[List[str]] = None
    job_type: Optional[str] = None
    remote_only: Optional[bool] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    page: int = 1
    per_page: int = 20


class ResumeUpload(BaseModel):
    user_id: str
    filename: str
    file_content: str  # Base64 encoded


class InterviewRequest(BaseModel):
    job_id: int = 0  # 0 for general practice, specific job ID for targeted questions
    user_id: str
    role: str  # Target role for question generation


class InterviewFeedback(BaseModel):
    overall_score: float
    technical_accuracy: float
    communication_score: float
    strengths: List[str]
    improvements: List[str]
    recommendations: List[Dict[str, str]]


class ResponseSubmission(BaseModel):
    transcript: str
    duration: float = 10.0


class SkillGapRequest(BaseModel):
    resume_text: str
    job_id: int


# Global instances
interview_system = InterviewPracticeSystem()
interview_sessions = {}  # In-memory storage for active sessions

# Initialize FastAPI
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Tech Jobs Crawler API...")
    
    # Initialize database
    from database import db_manager
    try:
        db_manager.connect()
        logger.info("Database connected successfully")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
    
    # Start LinkedIn Background Crawler (Bonus Feature)
    # import asyncio
    # from crawler.linkedin_crawler import start_background_crawler
    # asyncio.create_task(start_background_crawler())
    # logger.info("Background crawler started")
    
    yield
    
    # Cleanup
    db_manager.close()
    logger.info("Shutting down API...")

app = FastAPI(
    title="Tech Jobs Crawler API",
    description="API for tracking tech job openings and interview practice",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware - Allow all origins including file:// and null
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


# Initialize database with sample data
@app.get("/api/initialize")
async def initialize_database():
    """Initialize database with sample companies and jobs"""
    from database import db_manager, CompanyOperations, JobOperations
    
    # Ensure database is connected
    if not db_manager.engine:
        db_manager.connect()
    
    company_ops = CompanyOperations(db_manager)
    job_ops = JobOperations(db_manager)
    
    # Sample DFW tech companies
    sample_companies = [
        {"name": "AT&T", "industry": "Telecommunications", "location_city": "Dallas", "location_state": "TX", "website": "https://att.com"},
        {"name": "Toyota", "industry": "Automotive", "location_city": "Plano", "location_state": "TX", "website": "https://toyota.com"},
        {"name": "Southwest Airlines", "industry": "Aviation", "location_city": "Dallas", "location_state": "TX", "website": "https://swaconnect.com"},
        {"name": "Infosys", "industry": "Technology", "location_city": "Plano", "location_state": "TX", "website": "https://infosys.com"},
        {"name": "Accenture", "industry": "Consulting", "location_city": "Irving", "location_state": "TX", "website": "https://accenture.com"},
        {"name": "TCS", "industry": "Technology", "location_city": "Frisco", "location_state": "TX", "website": "https://tcs.com"},
        {"name": "Cognizant", "industry": "Technology", "location_city": "Dallas", "location_state": "TX", "website": "https://cognizant.com"},
        {"name": "Wipro", "industry": "Technology", "location_city": "Irving", "location_state": "TX", "website": "https://wipro.com"},
        {"name": "DocuSign", "industry": "Technology", "location_city": "Plano", "location_state": "TX", "website": "https://docusign.com"},
        {"name": "Comcast", "industry": "Telecommunications", "location_city": "Dallas", "location_state": "TX", "website": "https://comcast.com"},
    ]
    
    company_ids = []
    for company in sample_companies:
        try:
            company_id = company_ops.create(company)
            company_ids.append(company_id)
            logger.info(f"Created company: {company['name']}")
        except Exception as e:
            logger.debug(f"Company might exist: {e}")
    
    # Sample job postings
    sample_jobs = [
        {"company_id": 1, "title": "Senior Software Engineer", "location_city": "Dallas", "location_state": "TX", "experience_level": "senior", "salary_range": "$130K - $180K", "job_type": "Full-time", "description": "Looking for experienced software engineers to join our team.", "source_url": "https://careers.att.com"},
        {"company_id": 1, "title": "DevOps Engineer", "location_city": "Dallas", "location_state": "TX", "experience_level": "mid", "salary_range": "$100K - $140K", "job_type": "Full-time", "description": "Manage cloud infrastructure and CI/CD pipelines.", "source_url": "https://careers.att.com"},
        {"company_id": 2, "title": "Full Stack Developer", "location_city": "Plano", "location_state": "TX", "experience_level": "mid", "salary_range": "$110K - $150K", "job_type": "Full-time", "description": "Build web applications using React and Python.", "source_url": "https://careers.toyota.com"},
        {"company_id": 3, "title": "Data Scientist", "location_city": "Dallas", "location_state": "TX", "experience_level": "senior", "salary_range": "$140K - $190K", "job_type": "Full-time", "description": "Analyze flight data to improve operations.", "source_url": "https://careers.southwest.com"},
        {"company_id": 4, "title": "Cloud Architect", "location_city": "Plano", "location_state": "TX", "experience_level": "senior", "salary_range": "$150K - $200K", "job_type": "Full-time", "description": "Design cloud solutions on AWS and Azure.", "source_url": "https://careers.infosys.com"},
        {"company_id": 5, "title": "Java Developer", "location_city": "Irving", "location_state": "TX", "experience_level": "mid", "salary_range": "$90K - $130K", "job_type": "Full-time", "description": "Develop enterprise applications.", "source_url": "https://careers.accenture.com"},
        {"company_id": 6, "title": "Python Developer", "location_city": "Frisco", "location_state": "TX", "experience_level": "entry", "salary_range": "$70K - $100K", "job_type": "Full-time", "description": "Build automation scripts and data pipelines.", "source_url": "https://careers.tcs.com"},
        {"company_id": 7, "title": "Machine Learning Engineer", "location_city": "Dallas", "location_state": "TX", "experience_level": "senior", "salary_range": "$160K - $220K", "job_type": "Full-time", "description": "Develop ML models for business solutions.", "source_url": "https://careers.cognizant.com"},
        {"company_id": 8, "title": "Frontend Developer", "location_city": "Irving", "location_state": "TX", "experience_level": "mid", "salary_range": "$95K - $135K", "job_type": "Full-time", "description": "Build responsive web apps with React.", "source_url": "https://careers.wipro.com"},
        {"company_id": 9, "title": "Security Engineer", "location_city": "Plano", "location_state": "TX", "experience_level": "senior", "salary_range": "$140K - $180K", "job_type": "Full-time", "description": "Protect company systems and data.", "source_url": "https://careers.docusign.com"},
    ]
    
    job_count = 0
    for job in sample_jobs:
        try:
            job_ops.create(job)
            job_count += 1
            logger.info(f"Created job: {job['title']}")
        except Exception as e:
            logger.debug(f"Job creation note: {e}")
    
    return {
        "status": "success",
        "message": "Database initialized with sample DFW tech companies and jobs",
        "companies_created": len(company_ids),
        "jobs_created": job_count
    }


# Company endpoints
@app.get("/api/companies", response_model=List[CompanyResponse])
async def get_companies(
    city: Optional[str] = None,
    industry: Optional[str] = None,
    page: int = 1,
    per_page: int = 20
):
    """Get list of companies from database"""
    from database import db_manager, CompanyOperations
    
    if not db_manager.engine:
        db_manager.connect()
    
    company_ops = CompanyOperations(db_manager)
    offset = (page - 1) * per_page
    companies = company_ops.search(city=city, industry=industry, limit=per_page, offset=offset)
    return companies


@app.post("/api/companies", response_model=CompanyResponse)
async def create_company(company: CompanyCreate):
    """Create a new company in database"""
    from database import db_manager, CompanyOperations
    
    if not db_manager.engine:
        db_manager.connect()
    
    company_ops = CompanyOperations(db_manager)
    company_id = company_ops.create(company.dict())
    return {**company.dict(), "id": company_id, "created_at": datetime.utcnow()}


@app.get("/api/companies/{company_id}", response_model=CompanyResponse)
async def get_company(company_id: int):
    """Get company by ID from database"""
    from database import db_manager, CompanyOperations
    
    if not db_manager.engine:
        db_manager.connect()
    
    company_ops = CompanyOperations(db_manager)
    company = company_ops.get_by_id(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


# Job endpoints
@app.get("/api/jobs", response_model=List[JobResponse])
async def search_jobs(search: JobSearch = Depends()):
    """Search for jobs with various filters from database"""
    from database import db_manager, JobOperations
    
    if not db_manager.engine:
        db_manager.connect()
    
    # Check if we are using model_dump (Pydantic v2) or dict (v1)
    filters = search.model_dump() if hasattr(search, 'model_dump') else search.dict()
    
    job_ops = JobOperations(db_manager)
    jobs = job_ops.search(filters)
    return jobs


@app.post("/api/jobs", response_model=JobResponse)
async def create_job(job: JobCreate):
    """Create a new job posting in database"""
    from database import db_manager, JobOperations
    
    if not db_manager.engine:
        db_manager.connect()
    
    job_ops = JobOperations(db_manager)
    job_id = job_ops.create(job.dict())
    return {**job.dict(), "id": job_id, "created_at": datetime.utcnow()}


@app.post("/api/jobs/simple")
async def create_job_simple(job_data: Dict):
    """Simple job creation for crawler - doesn't require company_id"""
    from database import db_manager, JobOperations
    
    if not db_manager.engine:
        db_manager.connect()
    
    job_ops = JobOperations(db_manager)
    
    # Ensure we have required fields with defaults
    if 'company_id' not in job_data or job_data['company_id'] is None:
        # Try to get a random company ID or use 1
        try:
            from database import CompanyOperations
            company_ops = CompanyOperations(db_manager)
            companies = company_ops.search(limit=1)
            if companies:
                job_data['company_id'] = companies[0]['id']
            else:
                job_data['company_id'] = 1
        except:
            job_data['company_id'] = 1
    
    job_data['job_type'] = job_data.get('job_type') or 'full-time'
    job_data['status'] = 'active'
    
    try:
        job_id = job_ops.create(job_data)
        return {"id": job_id, "status": "success"}
    except Exception as e:
        logger.error(f"Error creating job: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/api/crawler/linkedin")
async def trigger_linkedin_crawl(background_tasks: BackgroundTasks):
    """Manually trigger a LinkedIn crawl cycle with dynamic variety"""
    from crawler.linkedin_crawler import LinkedInJobCrawler
    from config import config
    import random
    
    crawler = LinkedInJobCrawler()
    
    # Expanded keywords for variety
    all_keywords = [
        "Software Engineer", "Python Developer", "React Developer", 
        "Data Scientist", "DevOps Engineer", "Cloud Architect", 
        "Cybersecurity Analyst", "Machine Learning Engineer", 
        "Frontend Developer", "Backend Developer", "Java Developer",
        "Systems Engineer", "Mobile Developer", "Full Stack Engineer"
    ]
    
    # Shuffle keywords and pick a subset for this run
    random.shuffle(all_keywords)
    keywords = all_keywords[:4]
    
    # Shuffle cities to ensure different geographic coverage
    all_cities = config['crawler']['dfw_cities'][:]
    random.shuffle(all_cities)
    cities = all_cities[:5]
    
    logger.info(f"Triggering dynamic crawl: Keywords={keywords}, Cities={cities}")
    background_tasks.add_task(crawler.run_crawl, keywords, cities)
    return {"status": "started", "message": f"LinkedIn crawl started with {len(keywords)} rotating keywords across {len(cities)} cities."}

@app.post("/api/crawler/stop")
async def stop_linkedin_crawl():
    """Signal background LinkedIn crawl to stop"""
    from crawler.linkedin_crawler import LinkedInJobCrawler
    LinkedInJobCrawler.stop_requested = True
    return {"status": "success", "message": "Stop signal sent to crawler."}

@app.post("/api/database/clear")
async def clear_database():
    """Clear all companies and jobs from database (Danger Zone)"""
    from database import db_manager
    from sqlalchemy import text
    
    if not db_manager.engine:
        db_manager.connect()
        
    try:
        with db_manager.get_session() as session:
            # Delete jobs first due to foreign key constraints
            session.execute(text("DELETE FROM job_postings"))
            session.execute(text("DELETE FROM companies"))
            session.commit()
        return {"status": "success", "message": "Database cleared"}
    except Exception as e:
        logger.error(f"Error clearing database: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats")
async def get_db_stats():
    """Get live statistics from the database"""
    from database import db_manager
    from sqlalchemy import text
    
    if not db_manager.engine:
        db_manager.connect()
        
    try:
        with db_manager.get_session() as session:
            total_jobs = session.execute(text("SELECT COUNT(*) FROM job_postings")).scalar() or 0
            total_companies = session.execute(text("SELECT COUNT(*) FROM companies")).scalar() or 0
            remote_jobs = session.execute(text("SELECT COUNT(*) FROM job_postings WHERE location_remote = 1")).scalar() or 0
            
            remote_pct = round((remote_jobs / total_jobs * 100), 1) if total_jobs > 0 else 65.0
            
        return {
            "total_jobs": total_jobs,
            "total_companies": total_companies,
            "remote_jobs_pct": f"{remote_pct}%",
            "avg_salary": "$122K" # Dynamic salary analysis would require more schema updates
        }
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        return {
            "total_jobs": 0,
            "total_companies": 0,
            "remote_jobs_pct": "0%",
            "avg_salary": "N/A"
        }


@app.get("/api/jobs/simple")
async def get_jobs_simple():
    """Get all jobs - simplified for crawler view"""
    from database import db_manager, JobOperations
    
    if not db_manager.engine:
        db_manager.connect()
    
    job_ops = JobOperations(db_manager)
    return job_ops.search({"per_page": 100})


@app.get("/api/jobs/{job_id}")
async def get_job(job_id: int):
    """Get job details with requirements"""
    # In production, this would return full job details with extracted requirements
    return {
        "id": job_id,
        "title": "Software Engineer",
        "company": {"id": 1, "name": "Tech Corp"},
        "requirements": {
            "skills": [{"name": "Python", "category": "programming"}],
            "experience_years_min": 3,
            "experience_level": "mid"
        }
    }


@app.get("/api/jobs/{job_id}/similar")
async def get_similar_jobs(job_id: int, limit: int = 5):
    """Get similar jobs based on requirements"""
    return []


@app.get("/api/jobs/simple")
async def get_jobs_simple():
    """Get a list of all jobs for dropdowns"""
    from database.db_manager import DatabaseManager
    db = DatabaseManager()
    
    # Query all jobs with company names
    from sqlalchemy import text
    if not db.engine:
        db.connect()
        
    try:
        with db.get_session() as session:
            query = text("""
                SELECT j.id, j.title, c.name as company_name 
                FROM job_postings j
                JOIN companies c ON j.company_id = c.id
                ORDER BY j.id DESC
            """)
            result = session.execute(query)
            jobs = []
            for row in result:
                jobs.append({
                    "id": row.id,
                    "title": row.title,
                    "company_name": row.company_name
                })
            return jobs
    except Exception as e:
        logger.error(f"Error fetching simple jobs: {e}")
        return []


# Crawler endpoints
@app.post("/api/crawler/start")
async def start_crawler(background_tasks: BackgroundTasks):
    """Start the job crawler"""
    # In production, this would start the Celery tasks
    background_tasks.add_task(run_crawler_task)
    return {"message": "Crawler started", "status": "running"}


async def run_crawler_task():
    """Background task to run crawler"""
    logger.info("Running crawler task...")
    # Import and run crawler
    # from crawler.distributed_crawler import main
    # await main()


@app.get("/api/crawler/status")
async def get_crawler_status():
    """Get crawler status"""
    return {
        "status": "idle",
        "jobs_completed": 0,
        "last_run": None
    }


# Interview endpoints
@app.post("/api/interview/start")
async def start_interview(request: InterviewRequest):
    """Start an interview session with role-specific questions"""
    # Get job info if job_id provided (specific job questions)
    job_requirements = {}
    job_details = None
    if request.job_id > 0:
        try:
            from database import db_manager, JobOperations
            job_ops = JobOperations(db_manager)
            job = job_ops.get_by_id(request.job_id)
            if job:
                job_details = job
                # Extract skills and requirements from job description
                description = job.get('description', '').lower()
                skills = []
                
                # Common tech skills to look for in job descriptions
                skill_keywords = ['python', 'javascript', 'react', 'node.js', 'sql', 'aws', 'docker', 
                                'kubernetes', 'java', 'c#', '.net', 'postgresql', 'mongodb', 'git',
                                'linux', 'api', 'rest', 'graphql', 'microservices', 'agile', 'scrum']
                
                for skill in skill_keywords:
                    if skill in description:
                        skills.append({'name': skill.upper(), 'category': 'technical'})
                
                # If no specific skills found, infer from job title
                if not skills:
                    title = job.get('title', '').lower()
                    if 'software engineer' in title or 'developer' in title:
                        skills = [
                            {'name': 'PYTHON', 'category': 'programming'},
                            {'name': 'JAVASCRIPT', 'category': 'programming'},
                            {'name': 'DATABASE', 'category': 'backend'}
                        ]
                    elif 'frontend' in title or 'react' in title:
                        skills = [
                            {'name': 'REACT', 'category': 'frontend'},
                            {'name': 'JAVASCRIPT', 'category': 'programming'},
                            {'name': 'CSS', 'category': 'frontend'}
                        ]
                    elif 'backend' in title or 'api' in title:
                        skills = [
                            {'name': 'DATABASE', 'category': 'backend'},
                            {'name': 'API', 'category': 'backend'},
                            {'name': 'PYTHON', 'category': 'programming'}
                        ]
                    elif 'data scientist' in title:
                        skills = [
                            {'name': 'PYTHON', 'category': 'programming'},
                            {'name': 'STATISTICS', 'category': 'data'},
                            {'name': 'MACHINE LEARNING', 'category': 'ai'}
                        ]
                    elif 'devops' in title or 'cloud' in title:
                        skills = [
                            {'name': 'AWS', 'category': 'cloud'},
                            {'name': 'DOCKER', 'category': 'devops'},
                            {'name': 'CI/CD', 'category': 'devops'}
                        ]
                
                job_requirements = {
                    'title': job.get('title'),
                    'description': job.get('description'),
                    'company': job.get('company_name'),
                    'location': job.get('location_city', 'Remote'),
                    'skills_required': skills,
                    'experience_level': job.get('experience_level', 'mid'),
                    'specific_job': True
                }
        except Exception as e:
            logger.error(f"Error fetching job requirements: {e}")

    # Use role and job requirements to generate questions
    session = await interview_system.start_interview_session(
        job_requirements, 
        role=request.role,
        specific_job=job_details is not None
    )
    
    session_id = session['session_id']
    interview_sessions[session_id] = session
    
    return session


@app.post("/api/interview/{session_id}/respond")
async def submit_response(session_id: str, response: ResponseSubmission):
    """Submit interview response and get feedback"""
    if session_id not in interview_sessions:
        raise HTTPException(status_code=404, detail="Interview session not found")
    
    session = interview_sessions[session_id]
    current_idx = session['current_question_index']
    
    if current_idx >= len(session['questions']):
        raise HTTPException(status_code=400, detail="All questions completed")
    
    q_data = session['questions'][current_idx]
    question = InterviewQuestion(
        question_id=q_data['id'],
        question_text=q_data['text'],
        category=q_data['category'],
        difficulty=q_data['difficulty'],
        expected_keywords=q_data.get('expected_keywords', []),
        sample_answer=q_data.get('sample_answer', '')
    )
    
    feedback = await interview_system.analyze_response(question, response.transcript, response.duration)
    
    # Convert dataclass to dict for JSON serialization
    from dataclasses import asdict
    feedback_dict = asdict(feedback)
    
    # Store response
    response_entry = {
        'question_id': q_data['id'],
        'transcript': response.transcript,
        'feedback': feedback_dict
    }
    session['responses'].append(response_entry)
    session['current_question_index'] += 1
    
    return {"feedback": feedback_dict}


@app.post("/api/skills/analyze")
async def analyze_skill_gap(request: SkillGapRequest):
    """Analyze skills gap between resume and job description"""
    from database import job_ops
    job = job_ops.get_by_id(request.job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job lead not found")
        
    job_desc = job.get('description', '')
    
    analysis = await interview_system.llm.analyze_skill_gap(
        request.resume_text, 
        job_desc
    )
    
    if not analysis:
        from ai_modules.nlp_processor import JobRequirementExtractor, categorize_skill_gaps
        extractor = JobRequirementExtractor()
        job_reqs = extractor.extract(job_desc)
        user_skills = [s.strip() for s in request.resume_text.split() if len(s) > 3]
        analysis = categorize_skill_gaps(user_skills, job_reqs.skills_required)
    
    return analysis


async def _extract_text_from_file(file: UploadFile) -> str:
    """Helper to extract text from PDF, DOCX or TXT"""
    content = await file.read()
    filename = file.filename.lower()
    text = ""
    
    try:
        if filename.endswith('.pdf'):
            import PyPDF2
            import io
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
            for page in pdf_reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
        elif filename.endswith('.docx'):
            import docx
            import io
            doc = docx.Document(io.BytesIO(content))
            text = '\n'.join([para.text for para in doc.paragraphs])
        else:
            text = content.decode('utf-8')
        return text.strip()
    except Exception as e:
        logger.error(f"Text extraction error: {e}")
        return ""

@app.post("/api/skills/analyze-file")
async def analyze_skill_gap_file(job_id: int = Form(...), file: UploadFile = File(...)):
    """Directly analyze an uploaded file including scans/images via AI"""
    # 1. Read binary content
    file_content = await file.read()
    mime_type = file.content_type
    
    # 2. Fetch job description
    from database import job_ops
    job = job_ops.get_by_id(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job lead not found")
        
    job_desc = job.get('description', '')
    
    # 3. Analyze using AI native document processing (Gemini handles OCR)
    try:
        logger.info(f"Starting AI analysis for file: {file.filename} ({len(file_content)} bytes, {mime_type})")
        analysis = await interview_system.llm.analyze_skill_gap_file(
            file_content, 
            mime_type, 
            job_desc
        )
    except Exception as e:
        logger.error(f"AI File Analysis Exception: {e}")
        analysis = None
    
    if not analysis:
        # Fallback to local text extraction if AI fails
        logger.info("AI analysis failed or returned empty results, trying local extraction fallback...")
        await file.seek(0)
        resume_text = await _extract_text_from_file(file)
        if resume_text:
            logger.info("Local extraction succeeded, calling text-based AI analysis...")
            analysis = await interview_system.llm.analyze_skill_gap(resume_text, job_desc)
            
    if not analysis:
        logger.warning("All analysis methods failed for this file.")
        raise HTTPException(status_code=500, detail="Analysis failed. This often happens if the file content is unreadable or the AI service is busy.")
    
    logger.info("Analysis successfully completed.")
    return analysis

@app.post("/api/resume/parse")
async def parse_resume(file: UploadFile = File(...)):
    """Legacy/Manual extraction endpoint"""
    text = await _extract_text_from_file(file)
    return {"text": text, "filename": file.filename}


@app.post("/api/interview/{session_id}/end")
async def end_interview(session_id: str):
    """End interview session and get summary"""
    if session_id not in interview_sessions:
        raise HTTPException(status_code=404, detail="Interview session not found")
    
    session = interview_sessions[session_id]
    summary = await interview_system.end_session(session)
    
    # Clean up session
    # del interview_sessions[session_id] 
    
    return {"summary": summary}





# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# Run the application
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=app_config['app']['host'],
        port=app_config['app']['port'],
        reload=app_config['app'].get('debug', False),
        reload_dirs=[os.path.dirname(os.path.dirname(os.path.abspath(__file__)))]
    )
