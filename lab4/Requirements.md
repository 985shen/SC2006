# Functional and Non-Functional Requirements

---

## Functional Requirements

### FR1: Data retrieval via API

**FR1.1** - System must retrieve job vacancy data CSV file containing quarterly vacancy statistics by industry

**FR1.2** - System must retrieve SkillsFuture course directory excel file

---

### FR2: Display Top Industries by Job Vacancies

**FR2.1** - System must use the most recent quarter's data to calculate vacancy counts

**FR2.2** - System must identify and rank the top 10 industries with the highest job vacancy counts. Industries with fewer than 1,000 vacancies must be excluded from the ranking

**FR2.3** - System must display each industry with:
- Industry name
- Total vacancy count
- Growth rate (percentage change compared to the previous quarter)
- Rank indicator
- Industry icon

**FR2.4** - System must treat missing data marked as "na" in the dataset as zero vacancies

---

### FR3: Industry Selection

**FR3.1** - User must be able to select any industry from the top 10 list by clicking

**FR3.2** - System must visually indicate the currently selected industry card

**FR3.3** - System must allow users to change their selection at any time

---

### FR4: Course Retrieval and Display

**FR4.1** - System must match courses to industries using keyword matching on:
- Course title (`coursetitle`)

**FR4.2** - System must display up to 150 relevant courses per industry (depending on keyword matches available)

**FR4.3** - For each course, system must display:
- Course title (Clickable)
- Course provider name
- Duration (Hours)
- Course mode (Full-time / Part-time)
- Language
- Skill tags extracted from course title
- Course rating (Numerical)
- Number of respondents
- Full course fee (SGD)
- Subsidised course fee (SGD) with subsidy text
- Subsidy percentage
- Job impact level badge (High Impact / Medium Impact / Low Impact)

**FR4.4** - System must display a course detail modal when the course title is clicked, showing:
- Learning outcomes
- Prerequisites

---

### FR5: Course Filtering and Sorting

**FR5.1** - User must be able to filter courses by job impact level:
- All Impact Levels
- High Impact
- Medium Impact
- Low Impact

**FR5.2** - User must be able to filter courses by course mode:
- All Modes
- Full-time
- Part-time

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

**FR7.1** - System must only accept PDF files for resume upload and reject all other file formats with an error message

**FR7.2** - System must store the resume of the user

**FR7.3** - System must allow user to edit their resume

**FR7.4** - System must extract the skills of the user from their uploaded resume using keyword analysis, and store them grouped by category (e.g. Programming, Cloud & DevOps, Data & AI)

**FR7.5** - System must grade the uploaded resume out of 100 across three scored categories. Each section score is capped at its maximum (40, 30, 30 respectively) and the total is the sum of the three capped section scores:
- Impact (out of 40), covering sub-categories: action-oriented language, specifics and metrics, word over-usage, avoided filler words, positions of responsibility, and extra-curricular activities
- Presentation (out of 30), covering sub-categories: number of pages, contact information, and spell check
- Competencies (out of 30), covering sub-categories: analytical skills, communication skills, leadership skills, teamwork skills, and initiative skills

**FR7.6** - System must indicate whether the resume grade was produced using AI-enhanced analysis or standard rule-based analysis
- Subjective sub categories such as positions of responsibility, extra-curricular activities, analytical skills, communication skills, leadership skills, teamwork skills and initiative skills are graded by AI when available and fall back to rule-based if AI is unavailable
- Non-Subjective sub categories such as action-oriented language, specifics and metrics, word over-usage, avoided filler words, number of pages, contact information and spell check are rule-based regardless of AI availability

**FR7.7** - System must allow user to download their stored resume

**FR7.8** - System must allow user to delete their stored resume

**FR7.9** - System must recommend up to 6 courses whose prerequisites match the user's extracted skills, ranked by number of skill matches and then by course rating

---

### FR8: User Account Management

**FR8.1** - System must allow user to create an account

**FR8.2** - System must validate registration inputs: email must contain '@', password must be at least 6 characters, and full name must be at least 2 characters after whitespace trimming

**FR8.3** - System must normalise email addresses to lowercase and trim leading/trailing whitespace during registration

**FR8.4** - System must require users to enter their password twice during registration and reject the form if the two entries do not match

**FR8.5** - System must prevent registration with an email address that is already associated with an existing account

**FR8.6** - System must allow user to login to their account. Upon successful login, system must redirect the user to the page they originally attempted to access, or to the dashboard if no such page exists

**FR8.7** - System must allow users to log in with their email address regardless of letter casing

**FR8.8** - System must provide a "remember me" option during login to persist the user session

**FR8.9** - System must allow user to log out of their account, clearing their session and redirecting to the public page

**FR8.10** - System must allow user to favorite courses that they are interested in

**FR8.11** - System must allow user to remove courses from their favourites

**FR8.12** - System must display a dashboard after user has logged in that shows:
- Favourite Courses (with language filter)
- Resume Analyses count and latest resume score summary showing Impact, Presentation, and Competencies sub-scores
- Skills Profile showing extracted skills grouped by category
- Recommended courses based on user's extracted skills

---

## Non-Functional Requirements

### NFR1: Performance

**NFR1.1** - Dashboard with top 10 industries must load within 5 seconds

**NFR1.2** - Course search results must display within 3 seconds after industry selection

**NFR1.3** - Filter application must update results within 3 seconds

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

**NFR4.4** - System must verify that a user owns a resume analysis before allowing them to view it, and reject access with an error if the analysis belongs to a different user

---

### NFR5: Usability

**NFR5.1** - System must support both light theme and dark theme

---

### NFR6: Reliability

**NFR6.1** - System must gracefully handle API failures by falling back to cached data files when available

**NFR6.2** - System must display user-friendly error messages rather than raw exceptions when operations fail
