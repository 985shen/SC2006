from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.models.user import ResumeAnalysis
from app.services.resume_analysis_service import ResumeAnalysisService
from app.services.skill_extraction_service import SkillExtractionService
from app.services.resume_editor_service import ResumeEditorService
from datetime import datetime
import os
import json
from app.services.resume_grading_service import ResumeGradingService

resume_bp = Blueprint('resume', __name__, url_prefix='/resume')

ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    """Check whether the given filename has an allowed extension.

    Args:
        filename: Original filename string from the upload.

    Returns:
        bool: True if the extension is in ALLOWED_EXTENSIONS, False otherwise.
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_resume_analysis_service():
    """Create a ResumeAnalysisService using the current app configuration.

    Returns:
        ResumeAnalysisService: Configured service instance.
    """
    return ResumeAnalysisService(
        api_url=current_app.config.get('DEEPSEEK_API_URL', 'https://api.deepseek.com/v1/chat/completions'),
        model=current_app.config.get('DEEPSEEK_MODEL', 'deepseek-chat'),
        upload_folder=current_app.config.get('UPLOAD_FOLDER', 'uploads')
    )


def get_resume_editor_service():
    """Create a ResumeEditorService targeting the resumes upload folder.

    Returns:
        ResumeEditorService: Configured service instance.
    """
    return ResumeEditorService(upload_folder='uploads/resumes')


def get_skill_extraction_service():
    """Create a SkillExtractionService using the current app configuration.

    Returns:
        SkillExtractionService: Configured service instance.
    """
    return SkillExtractionService(
        api_url=current_app.config.get('DEEPSEEK_API_URL', 'http://localhost:11434/api/generate'),
        model=current_app.config.get('DEEPSEEK_MODEL', 'deepseek-r1:latest')
    )


def get_resume_grading_service():
    """Create a ResumeGradingService using the current app configuration.

    Returns:
        ResumeGradingService: Configured service instance.
    """
    return ResumeGradingService(
        ollama_url=current_app.config.get('DEEPSEEK_API_URL', 'http://localhost:11434/api/generate'),
        model=current_app.config.get('DEEPSEEK_MODEL', 'deepseek-r1:latest')
    )


@resume_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    """Handle resume upload for analysis or editing.

    On GET, renders the upload form.  On POST, saves the file, optionally
    runs AI analysis, skill extraction, and VMock-style grading, then
    redirects to the appropriate result or edit page.

    Returns:
        Response: Rendered upload form or redirect to result/edit page.
    """
    if request.method == 'POST':
        action = request.form.get('action', 'analyze')
        
        if 'resume' not in request.files:
            flash('No file uploaded', 'error')
            return redirect(request.url)
        
        file = request.files['resume']
        
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)
        
        if not allowed_file(file.filename):
            flash('Only PDF files are allowed', 'error')
            return redirect(request.url)
        
        try:
            # Get editor service
            resume_editor_service = get_resume_editor_service()
            
            # Save the uploaded file
            success, filepath, error = resume_editor_service.save_uploaded_resume(
                file, current_user.id, file.filename
            )
            
            if not success:
                flash(f'Error saving file: {error}', 'error')
                return redirect(request.url)
            
            # Verify file exists
            if not os.path.exists(filepath):
                flash(f'File was not saved correctly: {filepath}', 'error')
                return redirect(request.url)
            
            # Update user's resume path
            current_user.update_resume_path(filepath)
            
            # Route based on action
            if action == 'edit':
                return redirect(url_for('resume.edit'))
            else:
                # Get analysis service
                resume_analysis_service = get_resume_analysis_service()
                
                # CRITICAL FIX: File pointer was consumed by save_uploaded_resume()
                # We need to seek back to the beginning OR reopen the file
                file.seek(0)  # Reset file pointer to beginning
                
                # Analyze the resume - Pass file object and user_id
                success, analysis, message = resume_analysis_service.analyze_resume(file, current_user.id)
                
                if not success:
                    flash(f'Analysis failed: {message}', 'error')
                    return redirect(request.url)
                
                # Extract and store skills from the resume text
                try:
                    skill_service = get_skill_extraction_service()
                    # Re-read the saved resume file for skill extraction
                    from app.services.resume_analysis_service import ResumeAnalysisService as _RA
                    _ra = _RA(
                        api_url=current_app.config.get('DEEPSEEK_API_URL'),
                        model=current_app.config.get('DEEPSEEK_MODEL'),
                        upload_folder=current_app.config.get('UPLOAD_FOLDER')
                    )
                    resume_path = current_user.current_resume_path
                    if resume_path and os.path.exists(resume_path):
                        ok, resume_text, _ = _ra._extract_text_from_pdf(resume_path)
                        if ok and resume_text.strip():
                            skills, source = skill_service.extract_skills(resume_text)
                            current_user.set_skills(skills, source)
                except Exception as skill_err:
                    print(f"Skill extraction warning: {skill_err}")

                # VMock-style grading
                try:
                    grading_service = get_resume_grading_service()
                    resume_path = current_user.current_resume_path
                    if resume_path and os.path.exists(resume_path):
                        from app.services.resume_analysis_service import ResumeAnalysisService as _RA2
                        import pypdf
                        _ra2 = _RA2(
                            api_url=current_app.config.get('DEEPSEEK_API_URL'),
                            model=current_app.config.get('DEEPSEEK_MODEL'),
                            upload_folder=current_app.config.get('UPLOAD_FOLDER')
                        )
                        ok2, resume_text2, _ = _ra2._extract_text_from_pdf(resume_path)
                        if ok2 and resume_text2.strip():
                            page_count = 1
                            try:
                                with open(resume_path, 'rb') as pf:
                                    reader = pypdf.PdfReader(pf)
                                    page_count = len(reader.pages)
                            except Exception:
                                pass
                            grade_result = grading_service.grade(resume_text2, page_count)
                            analysis.grade_total = grade_result["total"]
                            analysis.grade_impact = grade_result["impact"]["score"]
                            analysis.grade_presentation = grade_result["presentation"]["score"]
                            analysis.grade_competencies = grade_result["competencies"]["score"]
                            analysis.grade_breakdown = json.dumps(grade_result)
                            analysis.grade_ollama_used = grade_result["ollama_online"]
                            db.session.commit()
                except Exception as grade_err:
                    print(f"Grading warning: {grade_err}")

                # Analysis object is already saved to database by the service
                # Just redirect to results
                return redirect(url_for('resume.result', analysis_id=analysis.id))
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            flash(f'An error occurred: {str(e)}', 'error')
            return redirect(request.url)
    
    # GET request - show upload form
    return render_template('resume/upload.html', has_resume=current_user.has_resume())


@resume_bp.route('/edit', methods=['GET'])
@login_required
def edit():
    """Render the resume editor pre-populated with extracted PDF content.

    Verifies the user has an uploaded resume on disk before proceeding.

    Returns:
        Response: Rendered resume/edit.html template or redirect on error.
    """
    if not current_user.has_resume():
        flash('Please upload a resume first', 'warning')
        return redirect(url_for('resume.upload'))
    
    try:
        # Check if file exists
        if not os.path.exists(current_user.current_resume_path):
            flash(f'Resume file not found: {current_user.current_resume_path}', 'error')
            current_user.current_resume_path = None
            current_user.resume_uploaded_at = None
            db.session.commit()
            return redirect(url_for('resume.upload'))
        
        # Get editor service
        resume_editor_service = get_resume_editor_service()
        
        # Extract resume data
        resume_data = resume_editor_service.extract_resume_data(current_user.current_resume_path)
        
        return render_template('resume/edit.html', resume_data=resume_data)
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        flash(f'Error loading resume: {str(e)}', 'error')
        return redirect(url_for('resume.upload'))


@resume_bp.route('/save-edited', methods=['POST'])
@login_required
def save_edited():
    """Save user-edited resume data and regenerate the PDF.

    Accepts a JSON payload describing the edited resume sections,
    generates a new PDF via ResumeEditorService, and updates the
    user's current resume path in the database.

    Returns:
        Response: JSON with success status and download URL, or error details.
    """
    if not current_user.has_resume():
        return jsonify({'success': False, 'error': 'No resume found'}), 400
    
    try:
        # Get editor service
        resume_editor_service = get_resume_editor_service()
        
        # Get edited data from request
        resume_data = request.json
        
        # CRITICAL FIX: Use absolute path from project root
        # Get project root (where run.py is located)
        from pathlib import Path
        project_root = Path(__file__).parent.parent.parent
        
        # Create user folder path with ABSOLUTE path
        user_folder = os.path.join(str(project_root), resume_editor_service.upload_folder, str(current_user.id))
        
        print(f"Project root: {project_root}")
        print(f"User folder will be: {user_folder}")
        
        # Ensure user folder exists with proper permissions
        if not os.path.exists(user_folder):
            os.makedirs(user_folder, mode=0o755)
            print(f"✓ Created user folder: {user_folder}")
        else:
            print(f"✓ User folder exists: {user_folder}")
        
        # Generate output filename
        timestamp = int(datetime.now().timestamp())
        output_filename = f'resume_edited_{timestamp}.pdf'
        output_path = os.path.join(user_folder, output_filename)
        
        print(f"Full output path: {output_path}")
        
        # Generate PDF
        success = resume_editor_service.generate_pdf(resume_data, output_path)
        
        if not success:
            return jsonify({'success': False, 'error': 'Failed to generate PDF'}), 500
        
        # Verify file was actually created
        if not os.path.exists(output_path):
            return jsonify({
                'success': False, 
                'error': f'PDF generation reported success but file not found at: {output_path}'
            }), 500
        
        # Verify file size
        file_size = os.path.getsize(output_path)
        if file_size == 0:
            return jsonify({
                'success': False,
                'error': f'PDF file was created but is empty (0 bytes)'
            }), 500
        
        print(f"✓ PDF created successfully: {output_path} ({file_size} bytes)")
        
        # Update user's current resume path
        current_user.update_resume_path(output_path)
        
        return jsonify({
            'success': True,
            'download_url': url_for('resume.download_resume'),
            'file_path': output_path,
            'file_size': file_size
        })
    
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in save_edited: {error_trace}")
        return jsonify({'success': False, 'error': str(e), 'trace': error_trace}), 500

@resume_bp.route('/download', methods=['GET'])
@login_required
def download_resume():
    """Serve the authenticated user's current resume PDF for download.

    Returns:
        Response: The PDF file as an attachment, or redirect on error.
    """
    if not current_user.has_resume():
        flash('No resume found', 'error')
        return redirect(url_for('resume.upload'))
    
    try:
        resume_path = current_user.current_resume_path
        
        print(f"Attempting to download: {resume_path}")
        
        # CRITICAL: Check if file exists before sending
        if not os.path.exists(resume_path):
            # File doesn't exist - clear from database
            print(f"✗ File not found: {resume_path}")
            current_user.current_resume_path = None
            current_user.resume_uploaded_at = None
            db.session.commit()
            
            flash(f'Resume file not found. Please upload a new resume.', 'error')
            return redirect(url_for('resume.upload'))
        
        # Check file size
        file_size = os.path.getsize(resume_path)
        print(f"✓ File exists: {resume_path} ({file_size} bytes)")
        
        if file_size == 0:
            flash('Resume file is empty. Please upload a new resume.', 'error')
            return redirect(url_for('resume.upload'))
        
        # Send file
        return send_file(
            resume_path,
            as_attachment=True,
            download_name='resume.pdf',
            mimetype='application/pdf'
        )
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        flash(f'Error downloading resume: {str(e)}', 'error')
        return redirect(url_for('resume.upload'))


@resume_bp.route('/result/<int:analysis_id>')
@login_required
def result(analysis_id):
    """Display the result page for a specific resume analysis.

    Ensures the analysis belongs to the current user before rendering.

    Args:
        analysis_id: Primary key of the ResumeAnalysis record.

    Returns:
        Response: Rendered resume/result.html or redirect if unauthorized.
    """
    analysis = ResumeAnalysis.query.get_or_404(analysis_id)
    
    # Ensure user owns this analysis
    if analysis.user_id != current_user.id:
        flash('Unauthorized access', 'error')
        return redirect(url_for('dashboard.index'))
    
    return render_template('resume/result.html', analysis=analysis)


@resume_bp.route('/delete', methods=['POST'])
@login_required
def delete_resume():
    """Delete the current user's resume file and clear the database reference.

    Returns:
        Response: JSON indicating success or failure.
    """
    if current_user.has_resume():
        try:
            # Delete the file
            if os.path.exists(current_user.current_resume_path):
                os.remove(current_user.current_resume_path)
                print(f"✓ Deleted file: {current_user.current_resume_path}")
            
            # Update database
            current_user.current_resume_path = None
            current_user.resume_uploaded_at = None
            db.session.commit()
            
            return jsonify({'success': True})
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500
    
    return jsonify({'success': False, 'error': 'No resume found'}), 404