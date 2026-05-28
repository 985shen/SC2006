"""Centralised industry-to-keyword mapping used for course filtering.

Each key is a normalised industry name and the value is a dict with a
'keywords' list.  Other services look up keywords here to decide whether
a course title is relevant to a given industry.
"""

INDUSTRY_KEYWORDS = {
    'information technology': {
        'keywords': [
            # Programming & Development
            'python', 'java', 'javascript', 'coding', 'programming', 'software', 'developer',
            'web', 'mobile', 'app', 'application', 'frontend', 'backend', 'fullstack', 'full stack',
            # Data & AI
            'data', 'analytics', 'ai', 'artificial intelligence', 'machine learning', 'deep learning',
            'neural', 'algorithm', 'big data', 'data science',
            # Infrastructure & Cloud
            'cloud', 'aws', 'azure', 'google cloud', 'devops', 'docker', 'kubernetes',
            'server', 'network', 'infrastructure', 'system admin',
            # Security
            'cyber', 'cybersecurity', 'security', 'hacking', 'penetration',
            # Database
            'database', 'sql', 'nosql', 'mongodb', 'postgresql',
            # Technologies
            'react', 'angular', 'vue', 'node', 'spring', 'django', 'flask',
            'api', 'rest', 'graphql', 'microservices',
            # General
            'it', 'tech', 'technology', 'digital', 'computer', 'computing',
            'agile', 'scrum', 'git', 'version control',
            'ux', 'ui', 'user interface', 'user experience', 'design thinking',
            'blockchain', 'cryptocurrency', 'iot', 'internet of things', 'robotics'
        ]
    },
    'healthcare': {
        'keywords': [
            # Core Healthcare
            'health', 'healthcare', 'medical', 'medicine', 'clinical', 'patient',
            'nursing', 'nurse', 'doctor', 'physician', 'practitioner',
            # Specialties
            'surgery', 'surgical', 'therapy', 'therapeutic', 'rehabilitation',
            'pharmacy', 'pharmaceutical', 'drug', 'medication',
            'dental', 'dentistry', 'oral health',
            # Care Types
            'elderly care', 'geriatric', 'pediatric', 'maternity', 'midwife',
            'mental health', 'psychology', 'psychiatric', 'counseling', 'wellness',
            'nutrition', 'dietetic', 'diet',
            # Settings
            'hospital', 'clinic', 'care home', 'hospice',
            # Procedures
            'diagnosis', 'treatment', 'care plan', 'assessment',
            'emergency', 'first aid', 'cpr', 'trauma', 'critical care', 'intensive care',
            # Allied Health
            'physiotherapy', 'occupational therapy', 'speech therapy',
            'radiology', 'imaging', 'laboratory', 'pathology',
            # Admin
            'medical records', 'health informatics', 'biomedical'
        ]
    },
    'financial': {
        'keywords': [
            # Core Finance
            'finance', 'financial', 'accounting', 'accountant', 'bookkeeping',
            'audit', 'auditor', 'tax', 'taxation',
            # Banking
            'banking', 'bank', 'credit', 'loan', 'mortgage',
            # Investment
            'investment', 'investor', 'trading', 'trader', 'stock', 'equity',
            'bond', 'forex', 'currency', 'fund', 'portfolio',
            'wealth', 'asset management',
            # Insurance
            'insurance', 'underwriting', 'claims', 'actuarial',
            # Corporate Finance
            'treasury', 'budget', 'budgeting', 'forecasting',
            'payroll', 'accounts payable', 'accounts receivable',
            # Analysis
            'financial analysis', 'financial modeling', 'valuation',
            # Tech
            'fintech', 'financial technology', 'payment', 'blockchain finance',
            # Compliance
            'compliance', 'regulation', 'aml', 'anti-money laundering', 'kyc',
            # Qualifications
            'cfa', 'cpa', 'acca', 'chartered', 'certified',
            # Tools
            'quickbooks', 'xero', 'sap finance', 'excel finance'
        ]
    },
    'engineering': {
        'keywords': [
            'engineering', 'engineer', 'mechanical', 'electrical', 'civil',
            'chemical', 'industrial', 'structural', 'aerospace',
            'design', 'cad', 'autocad', 'solidworks', 'catia',
            'manufacturing', 'production', 'assembly', 'fabrication',
            'machining', 'welding', 'maintenance', 'repair',
            'hvac', 'plumbing', 'piping', 'pump', 'motor', 'turbine',
            'generator', 'transformer', 'power systems',
            'automation', 'robotics', 'plc', 'scada', 'instrumentation',
            'quality control', 'testing', 'inspection', 'metrology',
            'project engineering', 'construction management',
            'renewable energy', 'solar', 'wind energy',
            'materials science', 'metallurgy'
        ]
    },
    'logistics': {
        'keywords': [
            'logistics', 'supply chain', 'procurement', 'purchasing', 'sourcing',
            'warehouse', 'warehousing', 'inventory', 'stock management',
            'distribution', 'shipping', 'freight', 'cargo', 'transport',
            'delivery', 'courier', 'fleet management',
            'customs', 'import', 'export', 'international trade',
            'forklift', 'material handling', 'packing', 'loading',
            'wms', 'warehouse management', 'erp logistics',
            'demand planning', 'forecasting', 'route optimization',
            'cold chain', 'dangerous goods', 'hazmat'
        ]
    },
    'sales': {
        'keywords': [
            'sales', 'selling', 'salesperson', 'account management',
            'business development', 'lead generation', 'prospecting',
            'negotiation', 'closing', 'deal making', 'pitch',
            'customer relationship', 'crm', 'client management',
            'revenue', 'target', 'quota', 'commission',
            'retail sales', 'wholesale', 'b2b sales', 'b2c sales',
            'field sales', 'inside sales', 'telemarketing', 'telesales',
            'account executive', 'sales engineer',
            'salesforce crm', 'hubspot'
        ]
    },
    'marketing': {
        'keywords': [
            'marketing', 'brand', 'branding', 'advertising', 'campaign',
            'promotion', 'content marketing', 'copywriting',
            'social media', 'digital marketing', 'online marketing',
            'seo', 'search engine optimization', 'sem', 'search engine marketing',
            'ppc', 'pay per click', 'google ads', 'facebook ads',
            'email marketing', 'newsletter', 'mailchimp',
            'analytics', 'google analytics', 'marketing metrics',
            'market research', 'consumer behavior', 'market segmentation',
            'influencer marketing', 'video marketing', 'content strategy',
            'graphic design', 'creative design', 'visual marketing'
        ]
    },
    'education': {
        'keywords': [
            'education', 'teaching', 'teacher', 'instructor', 'trainer',
            'training', 'facilitation', 'facilitator', 'learning',
            'curriculum', 'pedagogy', 'andragogy', 'instructional design',
            'elearning', 'e-learning', 'online learning', 'blended learning',
            'lms', 'learning management', 'course design',
            'assessment', 'evaluation', 'tutoring', 'coaching', 'mentoring',
            'adult learning', 'professional development',
            'early childhood', 'kindergarten', 'preschool',
            'special education', 'inclusive education'
        ]
    },
    'hospitality': {
        'keywords': [
            'hospitality', 'hotel', 'resort', 'accommodation', 'lodging',
            'tourism', 'travel', 'tour',
            'food', 'beverage', 'f&b', 'restaurant', 'cafe', 'catering',
            'banquet', 'event management', 'wedding planning',
            'housekeeping', 'front desk', 'reception', 'concierge',
            'guest service', 'customer service excellence',
            'culinary', 'chef', 'cook', 'cooking', 'kitchen',
            'bartender', 'barista', 'sommelier', 'wine service',
            'pastry', 'baking', 'food safety', 'haccp',
            'hotel management', 'revenue management'
        ]
    },
    'manufacturing': {
        'keywords': [
            'manufacturing', 'production', 'factory', 'plant',
            'assembly line', 'fabrication', 'machining', 'processing',
            'quality', 'quality control', 'quality assurance',
            'lean', 'lean manufacturing', 'six sigma', 'kaizen',
            'continuous improvement', 'process improvement',
            'iso', 'gmp', 'good manufacturing practice',
            'sop', 'standard operating procedure',
            'preventive maintenance', 'tpm', 'total productive maintenance',
            'oee', 'overall equipment effectiveness',
            '5s', 'visual management', 'kanban', 'jit', 'just in time',
            'capacity planning', 'production planning'
        ]
    },
    'creative': {
        'keywords': [
            'creative', 'design', 'designer', 'graphic design',
            'visual design', 'art', 'artist', 'illustration',
            'drawing', 'painting', 'sketching',
            'photography', 'photographer', 'photo editing',
            'video', 'videography', 'video editing', 'film',
            'animation', 'animator', 'motion graphics',
            'multimedia', 'digital media',
            'adobe', 'photoshop', 'illustrator', 'indesign',
            'premiere', 'after effects', 'final cut',
            'ux design', 'ui design', 'user interface', 'user experience',
            'web design', 'layout', 'typography', 'color theory',
            '3d modeling', '3d design', 'rendering',
            'portfolio development'
        ]
    },
    'construction': {
        'keywords': [
            'construction', 'building', 'contractor', 'site management',
            'project management construction', 'bim', 'building information',
            'architecture', 'architectural', 'structural design',
            'civil engineering', 'foundation', 'concrete', 'steel structure',
            'masonry', 'carpentry', 'joinery',
            'mep', 'mechanical electrical plumbing',
            'safety', 'workplace safety', 'bizSAFE', 'wsq safety',
            'scaffolding', 'rigging', 'lifting', 'crane operation',
            'excavation', 'earthwork', 'demolition',
            'renovation', 'refurbishment', 'fit-out',
            'painting', 'tiling', 'flooring', 'ceiling',
            'waterproofing', 'facade',
            'quantity surveying', 'cost estimation', 'tender',
            'building codes', 'regulations'
        ]
    }
}


def get_industry_keywords(industry: str) -> list:
    """Retrieve the keyword list associated with a given industry name.

    Performs exact and partial matching against the INDUSTRY_KEYWORDS map.

    Args:
        industry: Industry name to look up.

    Returns:
        list[str]: Matching keywords, or an empty list if none found.
    """
    if not industry:
        return []

    industry_lower = industry.lower()

    # Find matching keyword set
    for key, data in INDUSTRY_KEYWORDS.items():
        if key in industry_lower or industry_lower in key:
            return data['keywords']

    # Try partial matches
    for key, data in INDUSTRY_KEYWORDS.items():
        key_words = key.split()
        industry_words = industry_lower.split()
        if any(word in industry_words for word in key_words):
            return data['keywords']

    return []
