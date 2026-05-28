# Functional and Non-Functional Requirements

---

## Functional Requirements

### FR1: Data retrieval via API

**FR1.1** - System must retrieve job vacancy data CSV file containing quarterly vacancy statistics by industry

**FR1.2** - System must retrieve SkillsFuture course directory excel file

---

### FR2: Display Top Industries by Job Vacancies

**FR2.1** - System must use the most recent quarter's data to calculate vacancy counts

**FR2.2** - System must identify and rank the top 10 industries with the highest job vacancy counts

**FR2.3** - System must display each industry with:
- Industry name
- Total vacancy count
- Rank indicator
- Industry icon

**FR2.4** - System must handle missing data marked as "na" in dataset and exclude those industries

---

### FR3: Industry Selection

**FR3.1** - User must be able to select any industry from the top 10 list by clicking

**FR3.2** - System must highlight the selected industry card with a red light bar to indicate it is currently being selected

**FR3.3** - System must allow users to change their selection at any time

---

### FR4: Course Retrieval and Display

**FR4.1** - System must match courses to industries using keyword matching on:
- Course title (`coursetitle`)

**FR4.2** - System must display at least 10 relevant courses per industry (if available)

**FR4.3** - For each course, system must display:
- Course title (Clickable)
- Course provider name
- Duration (Hours)
- Course mode (Full-time / Part-time / Online)
- Language
- Skill tags extracted from course title
- Course rating (Numerical)
- Number of respondents
- Full course fee (SGD)
- Subsidised course fee (SGD) with subsidy text
- Job impact level badge (High Impact / Medium Impact / Low Impact)

**FR4.4** - System must display a course detail modal when the course title is clicked, showing:
- Learning outcomes
- Prerequisites

---

### FR5: Course Filtering and Search

**FR5.1** - User must be able to filter courses by job impact level:
- All Impact Levels
- High Impact
- Medium Impact
- Low Impact

**FR5.2** - User must be able to filter courses by course mode:
- All Modes
- Full-time
- Part-time
- Online

**FR5.3** - User must be able to filter by language of the course:
- All Languages
- English
- Mandarin
- Malay
- Tamil
- Others

**FR5.4** - User must be able to sort courses by:
- Highest Rating
- Lowest Price
- Shortest Duration

**FR5.5** - System must show the number of courses matching current filters

---

### FR6: Data Refresh

**FR6.1** - System must cache data files and refresh them when they are older than 24 hours to ensure the data are updated

---

### FR7: Resume Edit and Analysis

**FR7.1** - System must allow user to upload their resume

**FR7.2** - System must store the resume of the user

**FR7.3** - System must allow user to edit their resume

**FR7.4** - System must extract the skills of the user from their uploaded resume using keyword analysis, and store them grouped by category (e.g. Programming, Cloud & DevOps, Data & AI)

**FR7.5** - System must grade the uploaded resume out of 100 across three scored categories:
- Impact (out of 40), covering sub-categories: action-oriented language, specifics and metrics, word over-usage, avoided filler words, positions of responsibility, and extra-curricular activities
- Presentation (out of 30), covering sub-categories: number of pages, contact information, and spell check
- Competencies (out of 30), covering sub-categories: analytical skills, communication skills, leadership skills, teamwork skills, and initiative skills

**FR7.6** - System must indicate whether the resume grade was produced using AI-enhanced analysis or standard rule-based analysis
- Subjective sub categories such as positions of responsibility, extra-curricular activities, analytical skills, communication skills, leadership skills, teamwork skills and initiative skills are graded by AI when available and fall back to rule-based if AI is unavailable
- Non-Subjective sub categories such as action-oriented language, specifics and metrics, word over-usage, avoided filler words, number of pages, contact information and spell check are rule-based irregardless of AI availability

**FR7.7** - System must allow user to download their stored resume

**FR7.8** - System must allow user to delete their stored resume

---

### FR8: User Login

**FR8.1** - System must allow user to create an account

**FR8.2** - System must allow user to login to their account

**FR8.3** - System must allow user to favorite courses that they are interested in

**FR8.4** - System must display a dashboard after user has logged in that shows:
- Favourite Courses (with language filter)
- Resume Analyses count and latest resume score summary showing Impact, Presentation, and Competencies sub-scores
- Skills Profile showing extracted skills grouped by category

---

## Non-Functional Requirements

### NFR1: Performance

**NFR1.1** - Dashboard with top 10 industries must load within 5 seconds

**NFR1.2** - Course search results must display within 3 seconds after industry selection

**NFR1.3** - Filter application must update results within 3 second

---

### NFR2: Compatibility

**NFR2.1** - System must work on modern browsers:
- Chrome
- Firefox
- Safari

---

### NFR3: Maintainability

**NFR3.1** - CSS classes must follow consistent kebab-case naming conventions

**NFR3.2** - HTML template, Variables, Functions, Files and Database columns must follow consistent snake-case naming conventions

---

### NFR4: Security

**NFR4.1** - System must store user passwords as hashed values and must not store plaintext passwords

**NFR4.2** - System must restrict access to resume upload, resume editing, resume analysis, and dashboard pages to authenticated users only

**NFR4.3** - System must ensure that users can only view and manage their own resumes, analyses, and favourite courses

---

### NFR5: Usability

**NFR5.1** - System must support both light theme and dark theme

---










