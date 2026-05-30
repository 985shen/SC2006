import requests
import json
import os
from typing import Tuple, Dict, Any, Optional
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
import pypdf
from app.models.user import ResumeAnalysis
from app import db

class ResumeAnalysisService:
    """
    Service for analyzing resumes using DeepSeek AI
    
    Follows Single Responsibility Principle - handles only resume analysis
    """
    
    def __init__(self, api_url: str, model: str, upload_folder: str, timeout: int = 60):
        """
        Initialize resume analysis service
        
        Args:
            api_url: DeepSeek API endpoint
            model: Model name to use
            upload_folder: Directory for temporary file storage
            timeout: Request timeout in seconds
        """
        self.api_url = api_url
        self.model = model
        self.upload_folder = upload_folder
        self.timeout = timeout
        self._ensure_upload_folder_exists()
    
    def _ensure_upload_folder_exists(self) -> None:
        """Create upload folder if it doesn't exist"""
        if not os.path.exists(self.upload_folder):
            os.makedirs(self.upload_folder)
    
    def is_allowed_file(self, filename: str) -> bool:
        """Check if file has PDF extension"""
        return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'pdf'
    
    def analyze_resume(self, file: FileStorage, user_id: int) -> Tuple[bool, Optional[ResumeAnalysis], str]:
        """
        Analyze resume for action verbs and provide score
        
        Args:
            file: Uploaded PDF file
            user_id: User ID for saving analysis
            
        Returns:
            Tuple of (success, analysis_object, message)
        """
        # Validate file
        if not file or file.filename == '':
            return False, None, "No file selected"
        
        if not self.is_allowed_file(file.filename):
            return False, None, "Only PDF files are allowed"
        
        filename = secure_filename(file.filename)
        filepath = os.path.join(self.upload_folder, filename)
        
        try:
            # Save file temporarily
            file.save(filepath)
            
            # Extract text from PDF
            success, text, error = self._extract_text_from_pdf(filepath)
            if not success:
                self._delete_file(filepath)
                return False, None, error
            
            # Analyze with DeepSeek
            success, score, feedback, action_verbs = self._analyze_with_deepseek(text)
            if not success:
                self._delete_file(filepath)
                return False, None, feedback
            
            # Save analysis to database
            analysis = ResumeAnalysis(
                user_id=user_id,
                filename=filename,
                score=score,
                feedback=feedback,
                action_verbs_found=json.dumps(action_verbs)
            )
            db.session.add(analysis)
            db.session.commit()
            
            # Clean up file
            self._delete_file(filepath)
            
            return True, analysis, "Resume analyzed successfully"
            
        except Exception as e:
            self._delete_file(filepath)
            db.session.rollback()
            return False, None, f"Error analyzing resume: {str(e)}"
    
    def _extract_text_from_pdf(self, filepath: str) -> Tuple[bool, str, str]:
        """Extract text from PDF file"""
        try:
            with open(filepath, 'rb') as file:
                reader = pypdf.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                
                if not text.strip():
                    return False, "", "No text found in PDF"
                
                return True, text, ""
        except Exception as e:
            return False, "", f"Error extracting PDF text: {str(e)}"
    
    def _analyze_with_deepseek(self, text: str) -> Tuple[bool, int, str, list]:
        """
        Analyze resume text with DeepSeek AI
        
        Returns:
            Tuple of (success, score, feedback, action_verbs_list)
        """
        try:
            prompt = self._create_analysis_prompt(text)
            response = self._call_deepseek_api(prompt)
            
            if response['success']:
                return self._parse_analysis_response(response['content'])
            else:
                # Fallback to mock analysis if API fails
                return self._mock_analysis(text)
                
        except Exception as e:
            # Fallback to mock analysis
            return self._mock_analysis(text)
    
    def _create_analysis_prompt(self, text: str) -> str:
        """Create prompt for DeepSeek analysis.

        Instructs the model to return a JSON object with score,
        action_verbs, and feedback keys so that the response format
        is consistent with SkillExtractionService and AIScorer.
        """
        return f"""You are an expert resume reviewer. Analyze the following resume for the use of strong action verbs.

Strong action verbs include words like: "spearheaded", "orchestrated", "implemented", "developed", "led", "managed", "achieved", "created", "designed", "optimized", "streamlined", "executed", "launched", "pioneered", "transformed", etc.

Resume Text:
{text[:4000]}

Respond ONLY with valid JSON, no markdown fences, no extra text:
{{"score": <integer 1-10>, "action_verbs": [<list of action verb strings found, or empty list if none>], "feedback": "<detailed feedback explaining the score, what action verbs were found or missing, and specific recommendations for improvement>"}}

Important:
- Return ONLY the raw JSON object, nothing else
- score must be an integer from 1 to 10
- action_verbs must be a JSON array of strings
- feedback must be a single string with constructive, actionable advice
"""
    
    def _call_deepseek_api(self, prompt: str) -> Dict[str, Any]:
        """Make API call to DeepSeek"""
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False
            }
            
            response = requests.post(
                self.api_url,
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'content': result.get('response', '')
                }
            else:
                return {
                    'success': False,
                    'error': f"API returned status code {response.status_code}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _parse_analysis_response(self, content: str) -> Tuple[bool, int, str, list]:
        """Parse DeepSeek JSON response.

        Strips markdown code fences if present, extracts the first JSON
        object from the response, and validates the expected keys.  This
        parsing approach is consistent with AIScorer._parse_json and
        SkillExtractionService._extract_with_deepseek.
        """
        try:
            import re
            # Strip markdown code fences (```json ... ```)
            clean = re.sub(r"```json|```", "", content).strip()

            # Extract the first JSON object from the response
            match = re.search(r"\{.*\}", clean, re.DOTALL)
            if not match:
                return self._fallback_parse(content)

            data = json.loads(match.group())

            score = int(data.get("score", 5))
            score = max(1, min(10, score))

            action_verbs = data.get("action_verbs", [])
            if not isinstance(action_verbs, list):
                action_verbs = []
            action_verbs = [str(v).strip() for v in action_verbs if v]

            feedback = str(data.get("feedback", "")).strip()
            if not feedback:
                feedback = "Resume analyzed. See score and action verbs for details."

            return True, score, feedback, action_verbs

        except (json.JSONDecodeError, ValueError, TypeError):
            return self._fallback_parse(content)
        except Exception as e:
            return False, 5, f"Error parsing analysis: {str(e)}", []

    def _fallback_parse(self, content: str) -> Tuple[bool, int, str, list]:
        """Fallback parser for non-JSON responses.

        Handles cases where the model ignores the JSON instruction and
        returns the legacy SCORE:/ACTION_VERBS:/FEEDBACK: text format.
        """
        try:
            lines = content.strip().split('\n')
            score = 5
            action_verbs = []
            feedback = ""

            for line in lines:
                if line.startswith('SCORE:'):
                    score_str = line.replace('SCORE:', '').strip()
                    score = int(''.join(filter(str.isdigit, score_str)))
                    score = max(1, min(10, score))
                elif line.startswith('ACTION_VERBS:'):
                    verbs_str = line.replace('ACTION_VERBS:', '').strip()
                    if verbs_str.lower() != 'none':
                        action_verbs = [v.strip() for v in verbs_str.split(',') if v.strip()]

            if 'FEEDBACK:' in content:
                feedback_start = content.index('FEEDBACK:') + len('FEEDBACK:')
                feedback = content[feedback_start:].strip()

            if not feedback:
                feedback = "Resume analyzed. See score and action verbs for details."

            return True, score, feedback, action_verbs

        except Exception as e:
            return False, 5, f"Error parsing analysis: {str(e)}", []
    
    def _mock_analysis(self, text: str) -> Tuple[bool, int, str, list]:
        """Fallback mock analysis when API is unavailable"""
        # Simple keyword detection
        action_verbs = [
            "spearheaded", "orchestrated", "implemented", "developed", "led", 
            "managed", "achieved", "created", "designed", "optimized",
            "streamlined", "executed", "launched", "pioneered", "transformed"
        ]
        
        text_lower = text.lower()
        found_verbs = [verb for verb in action_verbs if verb in text_lower]
        
        # Calculate score based on number of action verbs found
        verb_count = len(found_verbs)
        if verb_count >= 10:
            score = 9
        elif verb_count >= 7:
            score = 8
        elif verb_count >= 5:
            score = 7
        elif verb_count >= 3:
            score = 6
        elif verb_count >= 1:
            score = 5
        else:
            score = 3
        
        if found_verbs:
            feedback = f"Good use of action verbs! Found {verb_count} strong action verbs. To improve further, consider adding more specific achievements and quantifiable results."
        else:
            feedback = "Your resume could benefit from stronger action verbs. Replace passive phrases with dynamic verbs like 'spearheaded', 'implemented', 'achieved', etc. This makes your accomplishments more impactful."
        
        return True, score, feedback, found_verbs
    
    def _delete_file(self, filepath: str) -> None:
        """Delete temporary file"""
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception as e:
            print(f"Warning: Could not delete file {filepath}: {str(e)}")
    
    def get_user_analyses(self, user_id: int):
        """Get all resume analyses for a user"""
        return ResumeAnalysis.query.filter_by(user_id=user_id).order_by(
            ResumeAnalysis.analyzed_at.desc()
        ).all()