"""Baseline benchmark for the CPU hotspots in jobvago.

Generates a realistic synthetic course-title dataset (~25k rows, the same
scale as the real SkillsFuture dataset) and a realistic resume, then times
the pure-Python implementations of the two dominant CPU paths:

  1. Per-request: industry-keyword filtering over the full course pool
     (CourseService.get_courses_data inner loop).
  2. Per-upload: resume grading (RuleBasedScorer) + skill-extraction fallback.
"""
import os, sys, time, random, statistics

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.industry_keywords import get_industry_keywords, INDUSTRY_KEYWORDS
from app.services.resume_grading_service import RuleBasedScorer
from app.services.skill_extraction_service import SkillExtractionService, SKILL_TAXONOMY

random.seed(42)

# ---------------------------------------------------------------------------
# Synthetic data generation (mirrors SkillsFuture course-title style)
# ---------------------------------------------------------------------------
PREFIXES = ["Certificate in", "Diploma in", "Advanced Diploma in", "WSQ",
            "Professional Certificate in", "Specialist Diploma in", "Course on",
            "Workshop:", "Masterclass in", "Foundation in", "Introduction to"]
TOPICS = ["Python Programming", "Data Analytics", "Cloud Computing with AWS",
          "Digital Marketing", "Financial Accounting", "Project Management",
          "Cybersecurity Essentials", "Machine Learning", "Graphic Design",
          "Supply Chain Logistics", "Nursing Care", "Culinary Arts",
          "Welding Technology", "Early Childhood Education", "Java Development",
          "Business Communication", "Retail Operations", "Hospitality Management",
          "Electrical Engineering", "Social Media Strategy", "Tax Computation",
          "Mobile App Development", "Network Administration", "UX UI Design",
          "Leadership and Team Management", "Mandarin Conversation",
          "Workplace Safety", "Robotics and Automation", "Bakery and Pastry",
          "Real Estate Salesmanship", "Aircraft Maintenance", "Veterinary Assisting"]
SUFFIXES = ["", "(Beginner)", "(Intermediate)", "(Advanced)", "for Professionals",
            "- Level 1", "- Level 2", "Bootcamp", "Fundamentals", "in Singapore",
            "for SMEs", "(Part-time)", "(WSQ Approved)"]

def make_titles(n):
    out = []
    for _ in range(n):
        out.append(" ".join(filter(None, [
            random.choice(PREFIXES), random.choice(TOPICS), random.choice(SUFFIXES)
        ])).strip())
    return out

TITLES = make_titles(25000)

RESUME = ("""John Tan | john.tan@example.com | 91234567
EDUCATION
National University of Singapore  Aug 2019 - May 2023
Bachelor of Computing, Honours
WORK EXPERIENCE
Acme Tech Pte Ltd  Jun 2023 - Present
Software Engineer
- Developed and deployed a microservices platform handling 2M requests daily
- Led a team of 5 engineers and mentored 3 junior developers
- Optimized database queries reducing latency by 40%
- Implemented CI/CD pipelines using Docker and Kubernetes
- Collaborated with product managers to design new features
INTERNSHIP EXPERIENCE
DataCorp  May 2022 - Aug 2022
Data Analyst Intern
- Analyzed customer datasets using Python and SQL
- Created dashboards in Tableau improving reporting efficiency by 30%
- Conducted statistical analysis and built regression models
LEADERSHIP & CO-CURRICULAR ACTIVITIES
- President of the Computing Club, organised 4 hackathons
- Captain of the university debate team
SKILLS
- Python, Java, JavaScript, SQL, Docker, Kubernetes, AWS, React, Machine Learning
- Leadership, communication, problem solving, teamwork
""" * 1)  # ~1 page; multiply to stress larger resumes

# ---------------------------------------------------------------------------
# Python implementations of the hot paths (copied from the services verbatim)
# ---------------------------------------------------------------------------
def py_filter_titles(titles, keywords, limit=150):
    matched = []
    for t in titles:
        tl = t.lower()
        if any(kw in tl for kw in keywords):
            matched.append(t)
            if len(matched) >= limit:
                break
    return matched

def py_grade(text):
    s = RuleBasedScorer()
    return (s.score_action_oriented(text), s.score_specifics(text),
            s.score_over_usage(text), s.score_avoided_words(text),
            s.score_contact_info(text),
            [s.score_competency(text, c) for c in
             ["analytical", "communication", "leadership", "teamwork", "initiative"]])

def py_skill_fallback(text):
    svc = SkillExtractionService("http://localhost:0", "x")
    return svc._extract_with_fallback(text)

# ---------------------------------------------------------------------------
# Timing helper
# ---------------------------------------------------------------------------
def timeit(fn, iters, *a):
    # warm
    fn(*a)
    samples = []
    for _ in range(iters):
        t = time.perf_counter()
        fn(*a)
        samples.append((time.perf_counter() - t) * 1000.0)
    return statistics.median(samples), min(samples), max(samples)

if __name__ == "__main__":
    print(f"Dataset: {len(TITLES)} course titles, resume {len(RESUME)} chars\n")

    # ---- 1. Course filtering (per request) ----
    # Common industry (matches early, hits 150-cap fast):
    it_kw = get_industry_keywords("information technology")
    # Rarer industry (few matches -> scans most of the list = worst case):
    rare_kw = get_industry_keywords("creative")  # fewer matching titles
    print(f"IT keywords: {len(it_kw)} | 'creative' keywords: {len(rare_kw)}")

    med, lo, hi = timeit(py_filter_titles, 30, TITLES, it_kw)
    n_it = len(py_filter_titles(TITLES, it_kw))
    print(f"[filter] IT (common, {n_it} matched): median {med:.2f} ms  (min {lo:.2f})")

    med, lo, hi = timeit(py_filter_titles, 15, TITLES, rare_kw)
    n_r = len(py_filter_titles(TITLES, rare_kw))
    print(f"[filter] creative ({n_r} matched, near full scan): median {med:.2f} ms  (min {lo:.2f})")

    # ---- 2. Resume grading (per upload) ----
    med, lo, hi = timeit(py_grade, 50, RESUME)
    print(f"\n[grade] RuleBasedScorer pipeline: median {med:.2f} ms  (min {lo:.2f})")

    # ---- 3. Skill extraction fallback (per upload) ----
    med, lo, hi = timeit(py_skill_fallback, 50, RESUME)
    print(f"[skills] regex fallback ({len(SKILL_TAXONOMY)} skills): median {med:.2f} ms  (min {lo:.2f})")
