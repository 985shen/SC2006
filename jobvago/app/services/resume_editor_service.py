import pdfplumber
import os
import re
import io
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Flowable
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

class ResumeEditorService:
    """
    Service for extracting, editing, and regenerating resume PDFs
    """
    
    def __init__(self, upload_folder: str = 'uploads/resumes'):
        """Initialise the resume editor service.

        Args:
            upload_folder: Relative path for storing user resume PDFs.
        """
        self.upload_folder = upload_folder
        self._ensure_upload_folder_exists()
    
    def _ensure_upload_folder_exists(self):
        """Create the upload directory tree if it does not already exist."""
        if not os.path.exists(self.upload_folder):
            os.makedirs(self.upload_folder)
    
    # ============================================================================
    # RESUME DATA EXTRACTION
    # ============================================================================
    
    def extract_resume_data(self, pdf_path: str) -> Dict:
        """Extract structured data from a resume PDF using pdfplumber.

        Args:
            pdf_path: Absolute path to the PDF file on disk.

        Returns:
            dict: Parsed resume with keys 'name', 'contact', and 'sections'.
        """
        with pdfplumber.open(pdf_path) as pdf:
            full_text = ""
            for page in pdf.pages:
                full_text += page.extract_text() + "\n"
        
        lines = [line.strip() for line in full_text.split('\n') if line.strip()]
        
        if not lines:
            return {'name': '', 'contact': '', 'sections': []}
        
        return self._parse_resume_lines(lines)
    
    def _parse_resume_lines(self, lines: List[str]) -> Dict:
        """Parse cleaned resume lines into a structured dictionary.

        Handles section header detection, organisation/date splitting, role
        extraction, and bullet-point grouping with special treatment for
        standalone sections like SKILLS and INTERESTS.

        Args:
            lines: List of non-empty, stripped text lines from the PDF.

        Returns:
            dict: Parsed resume with keys 'name', 'contact', and 'sections'.
        """
        name = ''
        contact = ''
        sections = []
        current_section = None
        current_entry = None
        
        SECTION_HEADERS = [
            'EDUCATION', 'EDUCATION AND QUALIFICATIONS',
            'WORK EXPERIENCE', 'INTERNSHIP EXPERIENCE', 'RELEVANT EXPERIENCES',
            'ACADEMIC PROJECTS', 'ENGINEERING PROJECTS', 'RESEARCH PROJECTS',
            'ACHIEVEMENTS', 'LEADERSHIP', 'CO-CURRICULAR ACTIVITIES', 
            'LEADERSHIP & CO-CURRICULAR ACTIVITIES', 'LEADERSHIP EXPERIENCE',
            'SKILLS', 'SKILLS AND INTEREST', 'SKILLS & INTEREST', 'SKILLS AND INTERESTS',
            'AWARDS', 'CERTIFICATIONS', 'ACADEMIC PROJECTS / EXPERIENCE',
            'LEADERSHIP / CO-CURRICULAR ACTIVITIES/ COMMUNITY SERVICES',
            'ACHIEVEMENTS, LEADERSHIP EXPERIENCE AND CO-CURRICULAR ACTIVITIES',
            'LEADERSHIP AND CO-CURRICULAR ACTIVITIES',
            'LEADERSHIP EXPERIENCE/ CO-CURRICULAR ACTIVITIES',
            'AWARDS AND ACHIEVEMENTS', 'AWARDS & ACHIEVEMENTS',
            'INTERESTS'
        ]
        
        # Sections that accumulate all bullets into ONE entry (not entry-based)
        STANDALONE_BULLET_SECTIONS = [
            'SKILLS', 'SKILLS AND INTEREST', 'SKILLS & INTEREST', 'SKILLS AND INTERESTS',
            'INTERESTS', 'AWARDS', 'CERTIFICATIONS', 'AWARDS AND ACHIEVEMENTS', 'AWARDS & ACHIEVEMENTS'
        ]
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Extract name and contact
            if i == 0 and not name:
                has_email = '@' in line
                has_phone = re.search(r'\d{8}', line)
                has_pipes = '|' in line
                
                if has_pipes and (has_email or has_phone):
                    parts = [p.strip() for p in line.split('|')]
                    name = parts[0]
                    contact = ' | '.join(parts[1:])
                    i += 1
                    continue
                else:
                    name = line
                    if i + 1 < len(lines):
                        next_line = lines[i + 1]
                        if '@' in next_line or re.search(r'\d{8}', next_line) or '|' in next_line:
                            contact = next_line
                            i += 2
                            continue
                    i += 1
                    continue
            
            if i == 1 and contact and (('@' in line or re.search(r'\d{8}', line)) and not self._is_section_header(line, SECTION_HEADERS)):
                i += 1
                continue
            
            # Check if section header
            if self._is_section_header(line, SECTION_HEADERS):
                # Save previous entry
                if current_entry and current_section:
                    current_section['entries'].append(current_entry)
                    current_entry = None
                
                current_section = {
                    'title': line,
                    'entries': []
                }
                sections.append(current_section)
                
                # For standalone bullet sections, create ONE entry immediately
                is_standalone_section = line.upper() in STANDALONE_BULLET_SECTIONS
                if is_standalone_section:
                    current_entry = {
                        'org': '',
                        'date': '',
                        'role': '',
                        'bullets': []
                    }
                
                i += 1
                continue
            
            # Process content in sections
            if current_section:
                # Check if this is a standalone bullet section (like SKILLS)
                is_standalone_section = current_section['title'].upper() in STANDALONE_BULLET_SECTIONS
                
                if line.startswith('•') or line.startswith('-') or line.startswith('●'):
                    bullet_text = line.lstrip('•-● ').strip()
                    
                    if is_standalone_section:
                        # For SKILLS/INTERESTS: Add all bullets to the ONE entry
                        if current_entry:
                            current_entry['bullets'].append(bullet_text)
                        else:
                            # Create the single entry if it doesn't exist
                            current_entry = {
                                'org': '',
                                'date': '',
                                'role': '',
                                'bullets': [bullet_text]
                            }
                    else:
                        # For WORK EXPERIENCE/EDUCATION: Attach bullet to current entry
                        if current_entry:
                            current_entry['bullets'].append(bullet_text)
                        else:
                            # Bullet without an entry - create empty entry
                            current_entry = {
                                'org': '',
                                'date': '',
                                'role': '',
                                'bullets': [bullet_text]
                            }
                    
                    i += 1
                    continue
                
                # Org + date detection (for regular sections)
                if not is_standalone_section:
                    date_match = self._extract_date_range(line)
                    
                    if date_match:
                        if current_entry:
                            current_section['entries'].append(current_entry)
                        
                        org, date = self._split_org_date(line)
                        
                        role = ''
                        if i + 1 < len(lines):
                            next_line = lines[i + 1]
                            if not next_line.startswith('•') and not self._is_section_header(next_line, SECTION_HEADERS):
                                if not self._extract_date_range(next_line):
                                    role = next_line
                                    i += 1
                        
                        current_entry = {
                            'org': org,
                            'date': date,
                            'role': role,
                            'bullets': []
                        }
                    else:
                        # Plain line in regular section → role if no role yet
                        if current_entry and not current_entry['role'] and not line.startswith('•'):
                            if not self._extract_date_range(line):
                                current_entry['role'] = line
                
                i += 1
                continue
            
            i += 1
        
        # Save last entry
        if current_entry and current_section:
            current_section['entries'].append(current_entry)
        
        return {
            'name': name,
            'contact': contact,
            'sections': sections
        }    
    def _is_section_header(self, line: str, headers: List[str]) -> bool:
        """Determine if a line is a resume section header.

        Matches against a known list of headers and also detects ALL-CAPS
        lines that are likely headers.

        Args:
            line: The text line to test.
            headers: List of known section header strings (uppercase).

        Returns:
            bool: True if the line is identified as a section header.
        """
        line_upper = line.upper().strip()
        
        if line_upper in headers:
            return True
        
        if line == line.upper() and len(line) > 3 and len(line) < 60:
            if not line.startswith('•') and not line.startswith('-'):
                if '@' not in line and not re.search(r'\d{8}', line):
                    return True
        
        return False
    
    def _extract_date_range(self, text: str) -> Optional[str]:
        """Extract a date range substring from the given text.

        Recognises patterns like 'Jan 2023 – Dec 2024', '2020 – Present', etc.

        Args:
            text: The text to scan for date ranges.

        Returns:
            str | None: The matched date range string, or None.
        """
        patterns = [
            r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}\s*[-–—]\s*(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}',
            r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}\s*[-–—]\s*Present',
            r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}\s*[-–—]\s*Current',
            r'\d{4}\s*[-–—]\s*\d{4}',
            r'\d{4}\s*[-–—]\s*Present',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        
        return None
    
    def _split_org_date(self, line: str) -> Tuple[str, str]:
        """Split an organisation name and date range from a single line.

        Args:
            line: The text line containing both organisation and date.

        Returns:
            Tuple of (organisation_name, date_range_string).
        """
        date_range = self._extract_date_range(line)
        
        if date_range:
            org = line.replace(date_range, '').strip()
            org = re.sub(r'[\|–—-]\s*$', '', org).strip()
            return org, date_range
        
        return line, ''
    
    # ============================================================================
    # PDF GENERATION
    # ============================================================================
    
    def generate_pdf(self, resume_data: Dict, output_path: str) -> bool:
        """Generate a formatted resume PDF from structured data using ReportLab.

        Produces a letter-sized PDF with a header, horizontal rules, and
        properly indented sections, entries, and bullet points.

        Args:
            resume_data: Dict with 'name', 'contact', and 'sections' keys.
            output_path: Absolute filesystem path for the output PDF.

        Returns:
            bool: True on success, False on failure.
        """
        try:
            # Register fonts for bullet support
            BODY_FONT = 'Helvetica'
            BOLD_FONT = 'Helvetica-Bold'
            
            # Try to register TrueType fonts for better bullet rendering
            for fp in ['/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                       '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf']:
                if os.path.exists(fp):
                    try:
                        pdfmetrics.registerFont(TTFont('TplBody', fp))
                        BODY_FONT = 'TplBody'
                    except:
                        pass
                    break
            
            for fp in ['/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
                       '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf']:
                if os.path.exists(fp):
                    try:
                        pdfmetrics.registerFont(TTFont('TplBold', fp))
                        BOLD_FONT = 'TplBold'
                    except:
                        pass
                    break
            
            # Define styles matching pdfeditor.py
            # Note: leftIndent=-6 counteracts SimpleDocTemplate's internal 6pt padding
            S_SECT = ParagraphStyle(
                'Sect', fontName=BOLD_FONT, fontSize=10, alignment=0, leading=13,
                leftIndent=-6, rightIndent=0, firstLineIndent=0, spaceAfter=2, spaceBefore=2
            )
            
            # Org/Date for use INSIDE Table cells (no negative indent)
            S_ORG_TBL = ParagraphStyle(
                'OrgTbl', fontName=BOLD_FONT, fontSize=10, alignment=0, leading=13,
                leftIndent=0, rightIndent=0, firstLineIndent=0, spaceAfter=0, spaceBefore=0
            )
            
            S_DATE_TBL = ParagraphStyle(
                'DateTbl', fontName=BODY_FONT, fontSize=10, alignment=2, leading=13,
                leftIndent=0, rightIndent=0, firstLineIndent=0, spaceAfter=0, spaceBefore=0
            )
            
            # Role/bullets for standalone use
            S_ROLE = ParagraphStyle(
                'Role', fontName=BODY_FONT, fontSize=10, alignment=0, leading=13,
                leftIndent=-6, rightIndent=0, firstLineIndent=0, spaceAfter=1, spaceBefore=0
            )
            
            S_BLT = ParagraphStyle(
                'Blt', fontName=BODY_FONT, fontSize=10, alignment=0, leading=13,
                leftIndent=0, rightIndent=0, firstLineIndent=-6, spaceAfter=1, spaceBefore=0
            )
            
            avail = 7.5 * inch  # usable width with 0.5in margins
            
            def esc(txt):
                """Escape text for ReportLab XML"""
                if not txt:
                    return ''
                return (str(txt).replace('&', '&amp;')
                               .replace('<', '&lt;')
                               .replace('>', '&gt;'))
            
            def org_date_row(org, date):
                """Two-column table: bold org left, date right"""
                lp = Paragraph(esc(org), S_ORG_TBL)
                rp = Paragraph(esc(date), S_DATE_TBL)
                tbl = Table([[lp, rp]], colWidths=[avail * 0.70, avail * 0.30])
                tbl.setStyle(TableStyle([
                    ('ALIGN',         (0, 0), (0, 0), 'LEFT'),
                    ('ALIGN',         (1, 0), (1, 0), 'RIGHT'),
                    ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
                    ('LEFTPADDING',   (0, 0), (-1, -1), 0),
                    ('RIGHTPADDING',  (0, 0), (-1, -1), 0),
                    ('TOPPADDING',    (0, 0), (-1, -1), 0),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                ]))
                return tbl
            
            def hr():
                """Horizontal rule matching template"""
                from reportlab.graphics.shapes import Drawing, Line
                
                class AbsoluteHR(Flowable):
                    """ReportLab Flowable that draws a full-width horizontal rule.

                    Renders a thin black line spanning the usable page width,
                    positioned with a small negative left offset to align with
                    the document margins.
                    """

                    def __init__(self):
                        Flowable.__init__(self)
                        self.width = 542
                        self.height = 1
                    
                    def draw(self):
                        self.canv.setStrokeColor(colors.black)
                        self.canv.setLineWidth(0.7)
                        self.canv.line(-7.4, 0.5, 534.7, 0.5)
                
                return AbsoluteHR()
            
            story = []
            
            # Header
            if resume_data.get('name') or resume_data.get('contact'):
                header_parts = []
                if resume_data.get('name'):
                    header_parts.append(f'<font size="13.9">{esc(resume_data["name"])}</font>')
                if resume_data.get('contact'):
                    sep = ' | ' if resume_data.get('name') else ''
                    header_parts.append(f'<font size="10">{esc(sep + resume_data["contact"])}</font>')
                
                header_text = ''.join(header_parts)
                
                S_HEADER = ParagraphStyle(
                    'Header', fontName=BOLD_FONT, fontSize=10, alignment=1,
                    leading=18, leftIndent=0, rightIndent=0, spaceAfter=0, spaceBefore=0
                )
                story.append(Paragraph(header_text, S_HEADER))
            
            story.append(hr())
            
            # Sections
            for section in resume_data.get('sections', []):
                # Section header + HR below
                story.append(Paragraph(esc(section.get('title', '')), S_SECT))
                story.append(hr())
                
                for entry in section.get('entries', []):
                    # Org + date row
                    if entry.get('org') or entry.get('date'):
                        story.append(org_date_row(entry.get('org', ''), entry.get('date', '')))
                    
                    # Role/degree
                    if entry.get('role'):
                        for role_line in entry['role'].split('\n'):
                            if role_line.strip():
                                story.append(Paragraph(esc(role_line.strip()), S_ROLE))
                    
                    # Bullets
                    for b in entry.get('bullets', []):
                        if b.strip():
                            story.append(Paragraph('\u2022 ' + esc(b), S_BLT))
                
                story.append(Spacer(1, 6))
            
            # Build PDF
            doc = SimpleDocTemplate(
                output_path,
                pagesize=letter,
                leftMargin=0.5*inch,
                rightMargin=0.5*inch,
                topMargin=0.5*inch,
                bottomMargin=0.5*inch
            )
            doc.build(story)
            
            return True
        
        except Exception as e:
            print(f"Error generating PDF: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    # ============================================================================
    # FILE MANAGEMENT
    # ============================================================================
    
    def save_uploaded_resume(self, file, user_id: int, filename: str) -> Tuple[bool, str, str]:
        """Save an uploaded resume file to the user's dedicated folder.

        Creates the user folder if necessary and generates a timestamped
        filename to avoid collisions.

        Args:
            file: Werkzeug FileStorage object from the upload.
            user_id: Numeric ID of the owning user.
            filename: Original filename (used only for extension validation).

        Returns:
            Tuple of (success, saved_filepath, error_message).
        """
        try:
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            user_folder = os.path.join(project_root, self.upload_folder, str(user_id))
            
            if not os.path.exists(user_folder):
                os.makedirs(user_folder, mode=0o755)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_filename = f"resume_{timestamp}.pdf"
            filepath = os.path.join(user_folder, safe_filename)
            
            file.save(filepath)
            
            if os.path.exists(filepath):
                return True, filepath, ""
            else:
                return False, "", f"File was not saved to {filepath}"
        
        except Exception as e:
            return False, "", str(e)
    
    def get_user_resume_path(self, user_id: int) -> Optional[str]:
        """Retrieve the filesystem path of the user's most recent resume PDF.

        Args:
            user_id: Numeric ID of the user.

        Returns:
            str | None: Path to the newest PDF, or None if no resumes exist.
        """
        user_folder = os.path.join(self.upload_folder, str(user_id))
        
        if not os.path.exists(user_folder):
            return None
        
        pdf_files = [f for f in os.listdir(user_folder) if f.endswith('.pdf')]
        
        if not pdf_files:
            return None
        
        pdf_files.sort(key=lambda x: os.path.getmtime(os.path.join(user_folder, x)), reverse=True)
        
        return os.path.join(user_folder, pdf_files[0])