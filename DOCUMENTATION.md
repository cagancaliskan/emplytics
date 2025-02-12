# Documentation: AI-Powered Open Source Resume System

## 1. Overview

The **AI-Powered Open Source Resume System** is a modern recruitment application designed to enhance the candidate selection process through AI-driven interviews and intelligent candidate-job matching. The system supports three main user roles:

- **Candidates**: Register, upload resumes (PDF/PNG), apply for job opportunities, and participate in AI-driven interview sessions.
- **HR Users**: Manage job postings, review candidate applications, schedule AI interviews, and analyze interview transcripts, AI scores, and CV matching percentages.
- **Administrators**: Oversee candidate profiles, track applications, and perform advanced candidate-job matching.

The system integrates traditional resume parsing with AI-driven interviews, making the hiring process more data-driven and efficient.

## 2. System Architecture

The project follows a modular design with distinct components:

### 2.1 Backend

- **Database & ORM**:
  - Uses **SQLAlchemy** and **SQLite** for persistent storage of candidates, jobs, applications, and interviews.
  - ORM Models:
    - `CandidateModel`, `AdminModel`, `HRModel`, `JobModel`, `InterviewModel`, `ApplicationModel`

- **Utility Functions**:
  - **Resume Parsing**: `parse_resume(file_path)` extracts text from PDF/PNG resumes using **PyPDF2**, **Pillow**, and **pytesseract**.
  - **Candidate-Job Matching**: `compute_matching_percentage(candidate, job)` uses **Sentence Transformers** to convert candidate skills and job requirements into vectors and compute cosine similarity.
  - **AI Question Generation**: `generate_dynamic_question(job_requirements, conversation_context)` uses **OpenAI ChatCompletion API** to generate dynamic interview questions.

- **RecruitmentSystemBackend**:
  - Handles candidate registration, login, job management, applications, and AI interview functionalities.

### 2.2 User Interface (UI)

- **PyQt5** for a multi-window desktop UI.
- UI components split into modules:
  - **ui_candidate.py**: Candidate login, registration, dashboard, AI interview.
  - **ui_hr.py**: HR job and interview management, transcript review.
  - **ui_admin.py**: Admin dashboard for candidate oversight.
  - **ui_main.py**: Main menu and application entry point.

- **Dark Mode & Futuristic UI** with a modern Qt stylesheet.

### 2.3 Project Structure

```
project/
├── backend.py         # ORM models, utility functions, backend logic
├── ui_candidate.py    # Candidate UI components
├── ui_hr.py           # HR UI components
├── ui_admin.py        # Admin UI components
├── ui_main.py         # Main menu and MainWindow logic
└── main.py            # Application entry point
```

## 3. Technical Components

### 3.1 Database Models (backend.py)

- **CandidateModel**: Stores candidate details (username, password, full name, resume text, key skills, application status).
- **JobModel**: Stores job details (company, title, description, required skills).
- **ApplicationModel**: Tracks candidate job applications.
- **InterviewModel**: Stores interview sessions, HR questions, transcripts, and AI scores.
- **AdminModel & HRModel**: Manage administrator and HR user credentials.

### 3.2 Resume Parsing

- **For PDFs**: Uses **PyPDF2** to extract text from each page.
- **For PNGs**: Uses **Pillow** and **pytesseract** for OCR-based text extraction.
- Extracted text is stored for candidate profiling and analysis.

### 3.3 Candidate-Job Matching

- **Vector Transformation**:
  - Uses `all-MiniLM-L6-v2` model from **Sentence Transformers** to convert candidate skills and job requirements into embeddings.
- **Cosine Similarity**:
  - Computes similarity between candidate and job embeddings to determine a CV matching percentage.

### 3.4 AI-Driven Interview Process

- **Dynamic Question Generation**:
  - `generate_dynamic_question(job_requirements, conversation_context)` sends job requirements and chat history to **OpenAI ChatCompletion API** for question generation.
- **Interview Flow**:
  - Candidates answer AI-generated questions through `CandidateAIInterviewDialog`.
  - AI dynamically adjusts follow-up questions.
  - The interview ends automatically after five responses.
- **Scoring Algorithm**:
  - AI assigns points based on response length (2 points per word, max score: 100).

### 3.5 Final Candidate Evaluation

- **Components**:
  - **CV Matching Percentage**: Computed via sentence embeddings and cosine similarity.
  - **AI Interview Score**: Score assigned based on AI interview performance.
- **Final Matching Calculation**:
  - The final matching percentage is the average of CV Matching Percentage and AI Interview Score (each weighted at 50%).
- **HR Dashboard**:
  - Displays candidate scores, CV matching, final matching percentage, and interview transcript.

## 4. User Workflows

### 4.1 Candidate Workflow

1. **Registration & Login**
   - Candidates register with personal details and upload resumes.
   - Parsed resume text is stored.
2. **Job Applications & AI Interview**
   - Candidates apply for jobs.
   - AI interviews generate dynamic questions based on job requirements.
   - AI evaluates responses and assigns a score.

### 4.2 HR Workflow

1. **Login & Job Management**
   - HR users log in and manage job postings.
2. **Interview Scheduling & Review**
   - HR schedules interviews with selected candidates.
   - After interviews, HR reviews AI scores and full transcripts.

### 4.3 Admin Workflow

1. **Login & Candidate Oversight**
   - Admins log in to oversee candidates and application statuses.
   - Perform candidate-job matching analysis.

## 5. Algorithms Used

- **Resume Parsing**: PyPDF2 (PDFs), Pillow & pytesseract (PNGs via OCR).
- **Sentence Embeddings**: all-MiniLM-L6-v2 model from **Sentence Transformers**.
- **Cosine Similarity**: Computes semantic similarity for candidate-job matching.
- **AI Question Generation**: OpenAI ChatCompletion API for generating interview questions.
- **AI Interview Scoring**: Word count-based scoring (max 100 points).
- **Final Matching Calculation**: Weighted average of CV matching and AI interview score.

## 6. Future Enhancements

- **Advanced Scoring**: Implement semantic coherence and sentiment analysis for AI interview scoring.
- **Dialogue Management**: Integrate Rasa or similar frameworks for more natural conversations.
- **Security & Deployment**: Secure API keys and sensitive data, consider Docker-based deployment.
- **Analytics & Reporting**: Develop HR/admin dashboards for tracking hiring trends and candidate performance.

## 7. Conclusion

The **AI-Powered Open Source Resume System** offers an intelligent and automated hiring solution. By integrating traditional resume parsing, AI-driven interview sessions, and advanced candidate-job matching techniques, the system provides a comprehensive and data-driven approach to recruitment.
