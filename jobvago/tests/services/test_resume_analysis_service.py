"""Unit tests for the ResumeAnalysisService."""

import pytest
from app.services.resume_analysis_service import ResumeAnalysisService

class TestResumeAnalysisMock:
    """Tests for ResumeAnalysisService mock/fallback analysis."""

    def setup_method(self):
        """Create a service instance."""
        self.service = ResumeAnalysisService(
            api_url="http://localhost:11434/api/generate",
            model="test-model",
            upload_folder="/tmp/test_uploads"
        )

    def test_mock_analysis_with_verbs(self):
        """Mock analysis detects action verbs and produces a score."""
        text = "I developed a platform and led the engineering team. We implemented CI/CD and optimized performance."
        success, score, feedback, verbs = self.service._mock_analysis(text)
        assert success is True
        assert score > 0
        assert len(verbs) > 0
        assert "developed" in verbs
        assert "led" in verbs

    def test_mock_analysis_no_verbs(self):
        """Mock analysis with no action verbs gives a low score."""
        text = "Worked on the project. Was responsible for tasks. Had various duties."
        success, score, feedback, verbs = self.service._mock_analysis(text)
        assert success is True
        assert score == 3
        assert len(verbs) == 0

    def test_mock_analysis_many_verbs(self):
        """Mock analysis with many verbs gives a high score."""
        text = ("developed led managed analyzed created implemented designed "
                "built launched optimized streamlined executed pioneered transformed achieved")
        success, score, feedback, verbs = self.service._mock_analysis(text)
        assert success is True
        assert score >= 8

    def test_is_allowed_file_pdf(self):
        """PDF files are allowed."""
        assert self.service.is_allowed_file("resume.pdf") is True
        assert self.service.is_allowed_file("Resume.PDF") is True

    def test_is_allowed_file_non_pdf(self):
        """Non-PDF files are rejected."""
        assert self.service.is_allowed_file("resume.docx") is False
        assert self.service.is_allowed_file("image.png") is False
        assert self.service.is_allowed_file("noextension") is False

    def test_parse_analysis_response_valid(self):
        """Valid response format is parsed correctly."""
        content = "SCORE: 7\nACTION_VERBS: developed, led, managed\nFEEDBACK: Good resume with strong verbs."
        success, score, feedback, verbs = self.service._parse_analysis_response(content)
        assert success is True
        assert score == 7
        assert "developed" in verbs
        assert "Good resume" in feedback

    def test_parse_analysis_response_no_verbs(self):
        """Response with 'None' verbs is parsed correctly."""
        content = "SCORE: 3\nACTION_VERBS: None\nFEEDBACK: Add more action verbs."
        success, score, feedback, verbs = self.service._parse_analysis_response(content)
        assert success is True
        assert score == 3
        assert verbs == []

    def test_parse_analysis_score_clamped(self):
        """Scores outside 1–10 range are clamped."""
        content = "SCORE: 15\nACTION_VERBS: developed\nFEEDBACK: Perfect."
        _, score, _, _ = self.service._parse_analysis_response(content)
        assert score == 10

        content2 = "SCORE: 0\nACTION_VERBS: None\nFEEDBACK: Needs work."
        _, score2, _, _ = self.service._parse_analysis_response(content2)
        assert score2 >= 1
