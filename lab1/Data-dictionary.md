# Data Dictionary

## Overview
This data dictionary documents the content of the 2 data sources used. 
Data retrieved from 2 APIs:
1. Job vacancies by industry (https://data.gov.sg/api/action/datastore_search?resource_id=d_f3bbdfbf92b811fff364aeed23b5e0bb)
2. SkillsFuture Course Directory (https://api-open.data.gov.sg/v1/public/api/datasets/d_b5802b76f409764c16dde4bf2feb19cd/poll-download)

## Glossary

| Term | Definition |
|------|------------|
| **Industry** | A category of business activity classified according to Singapore Standard Industrial Classification (SSIC) 2020. |
| **Job Vacancy** | An available job position within a specific industry during a particular quarter. Vacancy counts are aggregated quarterly and reported by the Ministry of Manpower Singapore. |
| **Quarter** | A 3 month period used for reporting job vacancy statistics. Quarters are labeled in the format YYYYNQ, where YYYY is the year and N is the quarter number between 1 to 4. For example, "20253Q" represents the third quarter (July to September) of 2025. |
| **Vacancy Count** | The total number of job vacancies available in an industry during a specific quarter. An integer value representing unfilled positions. When data is unavailable, the value is null. |
| **SSIC 2020** | Stands for Singapore Standard Industrial Classification 2020 which is the official standard for classifying economic activities in Singapore. |
| **SkillsFuture Course** | A training course eligible for SkillsFuture subsidies and credits. Courses are designed to help individuals develop job-relevant skills and advance their careers. |
| **Course Reference Number** | A unique identifier for each SkillsFuture course, following the format TGS-YYYYNNNNNN, where YYYY is the year and NNNNNN is a sequential number. For example: "TGS-2024044697". |
| **Training Provider** | An organization or institution approved to deliver SkillsFuture courses. Providers include universities, polytechnics, professional training institutes, and private education organizations. Each provider has a Unique Entity Number (UEN). |
| **Full Course Fee** | The total cost of a course in Singapore Dollars (SGD) before any subsidies are applied. Fees range from SGD 0 to over SGD 10,000. The fee covers all course materials, instruction, and assessments. |
| **Course Duration** | The total length of a course measured in hours. Courses typically range from 2 hours (short workshops) to 500+ hours (comprehensive programs). Duration helps users assess time commitment. |
| **Course Rating** | An average score between 0.0 to 5.0 stars given by past participants evaluating the overall quality of the course. Ratings are based on respondent feedback and indicate course satisfaction. |
| **Job Impact Rating** | A separate rating between 0.0 to 5.0 stars measuring how much the course helped participants in their job or career. This reflects practical career outcomes. |
| **Respondent Count** | The number of people who provided ratings or feedback for a course. Courses with higher respondent counts generally have more reliable ratings. Ratings may be null if fewer than 5 respondents. |
| **Attendance Count** | The total number of individuals who have enrolled in and attended a course since it was offered. This indicates course popularity and can range from 0 to 5,000+. |
| **Language** | The language(s) in which a course is conducted such as English, Mandarin, Tamil, and Malay. Some courses are offered in multiple languages. |
| **Course Description** | A text summary explaining what the course covers, the skills taught, and the learning approach to help users determine if a course matches their learning goals. |
| **Learning Outcomes** | A detailed description of the knowledge and skills a participant will gain by completing the course. |
| **Entry Requirements** | The prerequisites needed to enroll in a course. Requirements may include prior education, work experience, or specific skills. Some courses have no entry requirements. |
| **Top 10 Industries** | The ten industries with the highest number of job vacancies in the most recent quarter. |
| **Relevance Score** | A calculated value between 0.0 to 1.0 indicating how well a SkillsFuture course matches a selected industry. Higher scores indicate better matches. |
| **Industry-Course Mapping** | The relationship linking industries to relevant SkillsFuture courses. 1 industry can have many relevant courses, and 1 course can be relevant to multiple industries. |
| **API** | Application Programming Interface is a method for the application to retrieve data from external sources. |
| **Null Value** | Indicates missing or unavailable data. Common for optional fields like course ratings, fees, or historical job vacancy data. |
| **UEN (Unique Entity Number)** | A standardised identification number issued to businesses and organizations in Singapore. Each training provider has a UEN for official identification and verification purposes. |
| **Growth Rate** | The year-over-year percentage change in job vacancies for an industry, calculated as ((current_vacancies − previous_vacancies) / previous_vacancies) × 100. A positive value indicates increasing demand; a negative value indicates declining demand. Displayed with a '+' or '−' prefix and a '%' suffix (e.g. "+12.5%", "−3.2%"). |
| **Impact Level** | A categorical classification derived from the Job Impact Rating and course fee. Values are "High Impact" (rating ≥ 4.0, or fee ≥ SGD 10,000 when rating is 0 or null), "Medium Impact" (rating ≥ 3.0, or fee < SGD 10,000 when rating is 0 or null), or "Low Impact" (rating > 0 and < 3.0). Used for filtering courses on the dashboard. |
| **Subsidised Course Fee** | The net cost of a course in Singapore Dollars (SGD) after SkillsFuture subsidies have been applied. Calculated as the Full Course Fee minus the government subsidy amount. Can be SGD 0 for fully subsidised courses. |
| **Subsidy Percentage** | The percentage discount applied to a course, calculated as ((Full Course Fee − Subsidised Course Fee) / Full Course Fee) × 100. Ranges from 0% (no subsidy) to 100% (fully subsidised). Returns 0% if the Full Course Fee is SGD 0 to avoid division by zero. |
| **Course Mode** | The delivery format of a SkillsFuture course. Common values include "Part-time" and "Full-time". Used as a filter parameter on the course listing page. Defaults to "Part-time" when the source data is missing or null. |
| **Skill Tag** | A short label (e.g. "Python", "Data", "Cloud", "AI") extracted from a course title by keyword matching. Each course has up to 4 skill tags. If no keywords are matched, the default tag "Professional Development" is assigned. Skill tags help users quickly identify what a course covers. |
| **Action Verb** | A strong, results-oriented verb (e.g. "developed", "led", "implemented", "optimized") used in resume bullet points to describe accomplishments. The application maintains a set of 60+ recognised action verbs for scoring resumes. |
| **Resume Score** | An overall score from 1 to 10 assigned to a user's resume based on the presence and quality of action verbs. A higher score indicates stronger use of impactful language. Scores are generated by the DeepSeek AI model when available, or by a keyword-based fallback analyser. |
| **Resume Grade** | A comprehensive grade from 0 to 100 assessing resume quality across three weighted dimensions: Impact (40 points), Presentation (30 points), and Competencies (30 points). The total is the sum of the three sub-scores, capped at 100. |
| **Impact Sub-Score** | A sub-score from 0 to 40 evaluating the strength of a resume's content. Comprises six components: action verbs used (0–8), quantified achievements (0–8), word repetition penalty (0–6), filler word penalty (0–6), leadership positions (0–6), and extracurricular activities (0–6). |
| **Presentation Sub-Score** | A sub-score from 0 to 30 evaluating resume formatting and structure. Comprises three components: page count (0–10, with 1–2 pages scoring full marks), contact information presence (0–10, with 5 points each for phone and email), and spelling accuracy (0–10). |
| **Competencies Sub-Score** | A sub-score from 0 to 30 evaluating evidence of five competency categories: Analytical, Communication, Leadership, Teamwork, and Initiative. Each category is scored from 0 to 6 based on keyword matches or AI assessment. |
| **User Skill** | A skill identified from a user's uploaded resume, stored with its canonical name (e.g. "Python"), category (e.g. "Programming", "Data & AI", "Soft Skills"), and extraction source ("deepseek" for AI-extracted or "fallback" for regex-extracted). Skills are used to generate personalised course recommendations. |
| **Skill Category** | A classification grouping related skills together. Categories include "Programming", "Data & AI", "Cloud & DevOps", "Web Development", "Soft Skills", and others. Each skill in the taxonomy is assigned exactly one category. |
| **Favourite Course** | A course bookmarked by an authenticated user for later reference. The system stores a snapshot of the course's title, provider, and language at the time of bookmarking. A user can favourite multiple courses, and the same course can be favourited by multiple users. |
| **Password Hash** | A one-way cryptographic hash of the user's password generated using Werkzeug's security functions. The plaintext password is never stored. Authentication is performed by comparing a candidate password's hash against the stored hash. |
| **Course ID** | A 12-character deterministic identifier generated by computing the MD5 hash of the concatenated course title and provider name. This ensures the same course always produces the same ID regardless of when it is loaded. An explicit course ID can also be provided, in which case the auto-generated value is not used. |
















