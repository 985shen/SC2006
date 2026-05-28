from dataclasses import dataclass
from typing import List, Optional
import hashlib

@dataclass
class Industry:
    """Data-transfer object representing a job-market industry.

    Attributes:
        name: Display name of the industry (e.g. 'Information Technology').
        vacancies: Current number of open job vacancies.
        growth_rate: Year-over-year vacancy growth as a percentage.
        icon: Emoji icon used for UI display.
    """

    name: str
    vacancies: int
    growth_rate: float
    icon: str
    
    def get_growth_display(self) -> str:
        """Format the growth rate as a display string with a sign prefix.

        Returns:
            str: Growth rate prefixed with '+' or '-' and a '%' suffix.
        """
        sign = "+" if self.growth_rate >= 0 else ""
        return f"{sign}{self.growth_rate}%"

@dataclass
class Course:
    """Data-transfer object representing a SkillsFuture training course.

    Attributes:
        title: Course title (max 100 characters).
        provider: Name of the training provider.
        duration: Human-readable duration string (e.g. '40 hours').
        mode: Delivery mode such as 'Part-time' or 'Full-time'.
        rating: Average learner rating (1.0–5.0).
        reviews: Number of respondent reviews.
        price_original: Full course fee in SGD before subsidy.
        price_subsidized: Net fee after SkillsFuture subsidy.
        subsidy_text: Display text describing the subsidy (e.g. 'Up to 80% subsidy').
        impact_level: Categorised impact ('High Impact', 'Medium Impact', 'Low Impact').
        skills: List of skill tags extracted from the course title.
        language: Language of instruction (default: None).
        learning_outcomes: Description of what learners will gain (default: None).
        prerequisites: Prerequisite knowledge or experience (default: None).
        course_id: Unique identifier; auto-generated from title + provider if omitted.
    """

    title: str
    provider: str
    duration: str
    mode: str
    rating: float
    reviews: int
    price_original: int
    price_subsidized: int
    subsidy_text: str
    impact_level: str
    skills: List[str]
    language: Optional[str] = None
    learning_outcomes: Optional[str] = None
    prerequisites: Optional[str] = None
    course_id: Optional[str] = None
    
    def __post_init__(self):
        """Generate a deterministic course_id from title and provider if not provided."""
        if self.course_id is None:
            unique_string = f"{self.title}_{self.provider}"
            self.course_id = hashlib.md5(unique_string.encode()).hexdigest()[:12]
    
    def get_subsidy_percentage(self) -> int:
        """Calculate the subsidy percentage based on original and subsidised prices.

        Returns:
            int: Subsidy percentage (0-100).
        """
        if self.price_original == 0:
            return 0
        return int(((self.price_original - self.price_subsidized) / self.price_original) * 100)

@dataclass
class DashboardStats:
    """Aggregate statistics shown on the public career dashboard.

    Attributes:
        total_vacancies: Sum of vacancies across all tracked industries.
        top_industries: Number of industries displayed in the ranking.
        total_courses: Total number of courses available after filtering.
    """

    total_vacancies: int
    top_industries: int
    total_courses: int