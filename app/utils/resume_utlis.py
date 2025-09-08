import spacy
import re
import pandas as pd
import logging
from pathlib import Path
from typing import List, Dict, Set, Any

# Try to import openpyxl for Excel support
try:
    import openpyxl
    EXCEL_SUPPORT = True
except ImportError:
    EXCEL_SUPPORT = False
    # We'll log this warning only when actually trying to load Excel files

# Load English tokenizer, tagger, parser and NER
nlp = spacy.load("en_core_web_sm")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResumeParser:
    '''
    Enhanced resume parser with comprehensive information extraction capabilities.
    
    Features:
    - Robust name extraction with NER fallback
    - Multi-format phone number detection
    - Comprehensive email extraction
    - Advanced education pattern matching
    - Enhanced experience extraction
    - Comprehensive skills detection using NLP and skills databases
    - Data validation and cleaning
    - Error handling and logging
    '''

    def __init__(self, resume_text: str, required_skills: List[str]|None = None):
        '''
        Initialize ResumeParser with comprehensive error handling
        
        Args:
            resume_text: Raw text extracted from resume
            required_skills: Optional list of specific skills to look for
        '''
        try:
            if not resume_text or not resume_text.strip():
                raise ValueError("Resume text cannot be empty")
                
            self.resume_text = resume_text.strip()
            self.required_skills = required_skills if required_skills else []
            
            # Process with spaCy with error handling
            try:
                self.doc = nlp(self.resume_text)
            except Exception as e:
                logger.error(f"Error processing text with spaCy: {e}")
                self.doc = None
            
            # Parse resume sections
            self.sections = self._detect_and_parse_sections()
            logger.info(f"Detected {len(self.sections)} resume sections: {list(self.sections.keys())}")
                
            logger.info(f"Initialized ResumeParser with {len(self.resume_text)} characters")
            
        except Exception as e:
            logger.error(f"Error initializing ResumeParser: {e}")
            raise
    
    def _detect_and_parse_sections(self) -> Dict[str, str]:
        '''
        Detect and parse resume sections using multiple approaches
        
        Returns:
            Dict mapping section names to their content
        '''
        try:
            sections = {}
            lines = self.resume_text.split('\n')
            
            # Define section patterns and their aliases
            section_patterns = {
                'contact': ['contact', 'contact information', 'personal information', 'personal details'],
                'summary': ['summary', 'professional summary', 'career summary', 'profile', 'objective', 'career objective', 'professional objective'],
                'experience': ['experience', 'work experience', 'professional experience', 'employment', 'work history', 'career history', 'employment history', 'internships', 'internship experience', 'work', 'professional work'],
                'education': ['education', 'educational background', 'academic background', 'qualifications', 'academic qualifications', 'academic history'],
                'skills': ['skills', 'technical skills', 'core skills', 'key skills', 'competencies', 'core competencies', 'technical competencies', 'technologies', 'programming languages', 'tools'],
                'projects': ['projects', 'software engineering projects', 'personal projects', 'key projects', 'notable projects', 'project experience', 'research projects', 'academic projects'],
                'certifications': ['certifications', 'certificates', 'professional certifications', 'licenses', 'certification'],
                'achievements': ['achievements', 'accomplishments', 'awards', 'honors', 'recognition', 'publications', 'publications and patents', 'research publications'],
                'research': ['research', 'research experience', 'research work', 'publications', 'publications and patents'],
                'languages': ['languages', 'language skills', 'linguistic skills'],
                'interests': ['interests', 'hobbies', 'personal interests', 'activities'],
                'references': ['references', 'professional references']
            }
            
            # Method 1: Detect sections by headers (most reliable)
            current_section = None
            current_content = []
            
            # First pass: identify section headers and their boundaries
            section_boundaries = []
            for i, line in enumerate(lines):
                line_clean = line.strip()
                if not line_clean:
                    continue
                
                # Check if line is a potential section header
                if self._is_section_header(line_clean, section_patterns):
                    section_name = self._normalize_section_name(line_clean, section_patterns)
                    if section_name:
                        section_boundaries.append((i, section_name, line_clean))
            
            # Second pass: extract content between section boundaries
            for i, (start_idx, section_name, header) in enumerate(section_boundaries):
                # Determine end of section
                if i + 1 < len(section_boundaries):
                    end_idx = section_boundaries[i + 1][0]
                else:
                    end_idx = len(lines)
                
                # Extract section content (skip the header line)
                section_lines = []
                for j in range(start_idx + 1, end_idx):
                    if j < len(lines):
                        section_lines.append(lines[j])
                
                section_content = '\n'.join(section_lines).strip()
                if section_content:
                    sections[section_name] = section_content
            
            # Method 2: Handle header information (name, email, phone)
            # Usually in the first few lines
            header_lines = lines[:5]  # Check first 5 lines for contact info
            header_content = '\n'.join(header_lines).strip()
            if 'contact' not in sections and header_content:
                sections['contact'] = header_content
            
            # Method 3: Fallback pattern matching for common sections
            if not sections:  # If no sections detected by headers
                sections = self._fallback_section_detection()
            
            # Method 4: Special handling for skills sections with different formats
            if 'skills' in sections:
                # Check if skills section has subsections (like the sample resume)
                skills_content = sections['skills']
                if self._has_skill_subsections(skills_content):
                    sections['skills'] = self._parse_structured_skills(skills_content)
            
            logger.info(f"Section detection completed. Found sections: {list(sections.keys())}")
            return sections
            
        except Exception as e:
            logger.error(f"Error in section detection: {e}")
            return {'full_text': self.resume_text}  # Fallback to full text
    
    def _is_section_header(self, line: str, section_patterns: Dict) -> bool:
        '''
        Determine if a line is likely a section header
        '''
        line_lower = line.lower().strip()
        
        # Check for exact matches or close matches
        for section_type, patterns in section_patterns.items():
            for pattern in patterns:
                if pattern in line_lower:
                    return True
        
        # Additional heuristics for section headers
        # All uppercase and short
        if line.isupper() and 3 <= len(line.split()) <= 5:
            return True
        
        # Contains common section-like words and is formatted like a header
        section_keywords = ['summary', 'experience', 'education', 'skills', 'projects', 'certifications']
        if any(keyword in line_lower for keyword in section_keywords):
            # Check formatting (uppercase, underlined, etc.)
            if line.isupper() or line.replace(' ', '').replace('-', '').replace('_', '').isalpha():
                return True
        
        return False
    
    def _normalize_section_name(self, header: str, section_patterns: Dict) -> str:
        '''
        Normalize section header to standard section name
        '''
        header_lower = header.lower().strip()
        
        # Find best matching section type
        best_match = None
        best_score = 0
        
        for section_type, patterns in section_patterns.items():
            for pattern in patterns:
                if pattern in header_lower:
                    score = len(pattern) / len(header_lower)  # Prefer longer matches
                    if score > best_score:
                        best_score = score
                        best_match = section_type
        
        return best_match if best_match is not None else ""
    
    def _fallback_section_detection(self) -> Dict[str, str]:
        '''
        Fallback method for section detection using regex patterns
        '''
        sections = {}
        
        # Pattern-based section detection with more flexible patterns
        section_regexes = {
            'experience': r'(?i)(?:experience|employment|work\s+history|professional\s+experience|internships?|work)\s*:?\s*\n((?:(?!(?:education|skills|projects|certifications|publications)).)*?)(?=\n\s*(?:education|skills|projects|certifications|publications|$))',
            'education': r'(?i)(?:education|educational\s+background|academic)\s*:?\s*\n((?:(?!(?:experience|skills|projects|certifications|publications)).)*?)(?=\n\s*(?:experience|skills|projects|certifications|publications|$))',
            'skills': r'(?i)(?:skills|technical\s+skills|competencies|programming\s+languages|tools)\s*:?\s*\n((?:(?!(?:experience|education|projects|certifications|publications)).)*?)(?=\n\s*(?:experience|education|projects|certifications|publications|$))',
            'projects': r'(?i)(?:projects|software\s+engineering\s+projects|research\s+projects)\s*:?\s*\n((?:(?!(?:experience|education|skills|certifications|publications)).)*?)(?=\n\s*(?:experience|education|skills|certifications|publications|$))',
            'research': r'(?i)(?:research|publications|publications\s+and\s+patents)\s*:?\s*\n((?:(?!(?:experience|education|skills|projects|certifications)).)*?)(?=\n\s*(?:experience|education|skills|projects|certifications|$))'
        }
        
        for section_name, pattern in section_regexes.items():
            matches = re.findall(pattern, self.resume_text, re.MULTILINE | re.DOTALL)
            if matches:
                sections[section_name] = matches[0].strip()
        
        # Special handling: Look for experience patterns in the entire text if not found in sections
        if 'experience' not in sections or not sections['experience']:
            # Look for date + job title patterns anywhere in the text
            experience_patterns = [
                r'(?i)((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}\s+(?:research\s*)?intern[^\n]*(?:\n[^\n]*)*?)(?=\n\s*(?:[A-Z]|$))',
                r'(?i)(\d{4}[-\s]+\d{4}[^\n]*(?:intern|engineer|developer|analyst)[^\n]*(?:\n[^\n]*)*?)(?=\n\s*(?:[A-Z]|$))'
            ]
            
            experience_text = ''
            for pattern in experience_patterns:
                matches = re.findall(pattern, self.resume_text, re.MULTILINE | re.DOTALL)
                for match in matches:
                    if len(match.strip()) > 20:  # Ensure meaningful content
                        experience_text += match.strip() + '\n\n'
            
            if experience_text.strip():
                sections['experience'] = experience_text.strip()
        
        return sections
    
    def _has_skill_subsections(self, skills_content: str) -> bool:
        '''
        Check if skills section has structured subsections
        '''
        # Look for patterns like "JavaScript:", "Mobile:", "Java:"
        subsection_pattern = r'^\s*[A-Za-z][A-Za-z\s/]+:\s*'
        lines = skills_content.split('\n')
        
        subsection_count = 0
        for line in lines:
            if re.match(subsection_pattern, line.strip()):
                subsection_count += 1
        
        return subsection_count >= 2  # At least 2 subsections
    
    def _parse_structured_skills(self, skills_content: str) -> str:
        '''
        Parse structured skills section (like JavaScript:, Mobile:, etc.)
        '''
        lines = skills_content.split('\n')
        parsed_skills = []
        
        current_category = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if line is a category header (ends with colon)
            if ':' in line and not line.endswith(':'):
                # Split category and skills
                parts = line.split(':', 1)
                if len(parts) == 2:
                    category = parts[0].strip()
                    skills = parts[1].strip()
                    if skills:
                        parsed_skills.append(f"{category}: {skills}")
            elif line.endswith(':'):
                current_category = line[:-1].strip()
            elif current_category:
                # Skills belonging to current category
                parsed_skills.append(f"{current_category}: {line}")
                current_category = None  # Reset after first line
            else:
                # Standalone skills
                parsed_skills.append(line)
        
        return '\n'.join(parsed_skills)

    def extract_name(self)->str:
        '''
        Extract name from resume_text with improved robustness
        '''
        lines = [line.strip() for line in self.resume_text.strip().split('\n') if line.strip()]
        
        # Common titles to remove
        titles = ['mr', 'mrs', 'ms', 'dr', 'prof', 'professor', 'sir', 'madam']
        
        # Try first few lines for potential names
        for i, line in enumerate(lines[:3]):
            # Skip lines with common resume headers or contact info
            if any(keyword in line.lower() for keyword in ['resume', 'cv', 'curriculum vitae', '@', 'phone', 'email', 'address']):
                continue
                
            # Clean line by removing titles and extra whitespace
            words = line.split()
            cleaned_words = []
            for word in words:
                clean_word = re.sub(r'[^a-zA-Z\s]', '', word).lower()
                if clean_word not in titles and len(clean_word) > 1:
                    cleaned_words.append(word)
            
            # If we have 2-4 words (typical name range), consider it a name
            if 2 <= len(cleaned_words) <= 4:
                potential_name = ' '.join(cleaned_words)
                # Validate it looks like a name (only letters, spaces, some punctuation)
                if re.match(r'^[A-Za-z\s\.\-\']+$', potential_name):
                    return potential_name.title()
        
        # Fallback to NER if first few lines don't contain obvious names
        if self.doc is not None:
            for ent in self.doc.ents:
                if ent.label_ == 'PERSON':
                    # Additional validation for person entities
                    name_parts = ent.text.split()
                    if 2 <= len(name_parts) <= 4 and all(len(part) > 1 for part in name_parts):
                        return ent.text.title()
        
        return ""

    def extract_phone(self)->str:
        '''
        Extract phone number from resume_text with enhanced patterns

        examples : 
        9861289352
        +91 9861289352
        123-456-7890
        (123) 456 7890
        +1-555-123-4567
        555.123.4567 ext 123
        '''
        # Multiple regex patterns for different phone formats
        phone_patterns = [
            r'\+?\d{1,3}[\s\-\.]?\(?\d{3}\)?[\s\-\.]?\d{3}[\s\-\.]?\d{4}(?:[\s\-]?(?:ext|x|extension)[\s\.]?\d{1,5})?',  # International with optional extension
            r'\(?\d{3}\)?[\s\-\.]?\d{3}[\s\-\.]?\d{4}(?:[\s\-]?(?:ext|x|extension)[\s\.]?\d{1,5})?',  # US format with optional extension
            r'\+\d{1,3}[\s\-]?\d{3,4}[\s\-]?\d{3,4}[\s\-]?\d{3,4}',  # International format
            r'\d{10}',  # 10 digit number
            r'\+\d{1,3}\s?\d{8,12}',  # International simple format
        ]
        
        for pattern in phone_patterns:
            phones = re.findall(pattern, self.resume_text)
            if phones:
                # Clean and validate the first match
                phone = phones[0]
                # Remove extra spaces and normalize
                cleaned_phone = re.sub(r'\s+', ' ', phone.strip())
                # Basic validation - should have 7-15 digits
                digits_only = re.sub(r'\D', '', cleaned_phone)
                if 7 <= len(digits_only) <= 15:
                    return cleaned_phone
        
        return ""
    
    def extract_email(self)->str:
        '''
        Extract email from resume_text
        '''
        email_regex = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
        emails = re.findall(email_regex, self.resume_text)
        return emails[0] if emails else ""
    def _load_skills_database(self) -> Set[str]:
        '''
        Load comprehensive skills database from Excel file and predefined lists
        '''
        skills_set = set()
        
        try:
            # Try to load from Excel file first
            xlsx_path = Path("app/utils/skills_dataset.xlsx")
            if xlsx_path.exists():
                if not EXCEL_SUPPORT:
                    logger.warning("openpyxl not available. Excel files cannot be read. Install with: pip install openpyxl")
                    logger.info("Falling back to CSV and predefined skills...")
                else:
                    try:
                        df = pd.read_excel(xlsx_path)
                        logger.info(f"Loaded Excel skills database with columns: {df.columns.tolist()}")
                        
                        # Handle different possible column names for skills
                        skill_columns = []
                        for col in df.columns:
                            if any(keyword in col.lower() for keyword in ['skill', 'technology', 'tool', 'language']):
                                skill_columns.append(col)
                        
                        # If no specific skill columns found, try common column names
                        if not skill_columns:
                            common_names = ['Skills', 'Skill', 'Technology', 'Technologies', 'Tool', 'Tools']
                            for name in common_names:
                                if name in df.columns:
                                    skill_columns.append(name)
                                    break
                        
                        # Process skill columns
                        for col in skill_columns:
                            for skills_str in df[col].dropna():
                                skills_str = str(skills_str).strip()
                                if skills_str and skills_str.lower() not in ['nan', 'none', 'null']:
                                    # Handle different separators
                                    separators = [',', ';', '|', '\n']
                                    skills_list = [skills_str]  # Start with the whole string
                                    
                                    for separator in separators:
                                        if separator in skills_str:
                                            skills_list = [skill.strip() for skill in skills_str.split(separator)]
                                            break
                                    
                                    # Add individual skills
                                    for skill in skills_list:
                                        skill = skill.strip()
                                        if len(skill) > 2 and not skill.isdigit():  # Filter out very short strings and numbers
                                            skills_set.add(skill.lower())
                        
                        logger.info(f"Loaded {len(skills_set)} skills from Excel database")
                        
                    except Exception as e:
                        logger.warning(f"Could not load skills from Excel file: {e}. Trying CSV fallback...")
                        
                        # Fallback to CSV if Excel fails
                        csv_path = Path("app/job_skills.csv")
                        if csv_path.exists():
                            try:
                                df = pd.read_csv(csv_path)
                                if 'Skills' in df.columns:
                                    for skills_str in df['Skills'].dropna():
                                        # Parse comma-separated skills
                                        skills_list = [skill.strip() for skill in str(skills_str).split(',')]
                                        for skill in skills_list:
                                            if len(skill) > 2:  # Filter out very short strings
                                                skills_set.add(skill.lower())
                                    logger.info(f"Loaded {len(skills_set)} skills from CSV fallback")
                            except Exception as csv_error:
                                logger.warning(f"CSV fallback also failed: {csv_error}")
        except Exception as e:
            logger.warning(f"Could not load skills from database files: {e}")
        
        # Add comprehensive predefined skills
        predefined_skills = {
            # Programming Languages
            'python', 'java', 'javascript', 'c++', 'c#', 'ruby', 'php', 'swift', 'kotlin',
            'typescript', 'go', 'rust', 'scala', 'r', 'matlab', 'sql', 'html', 'css',
            
            # Frameworks & Libraries
            'react', 'angular', 'vue', 'node.js', 'express', 'django', 'flask', 'spring',
            'tensorflow', 'pytorch', 'keras', 'opencv', 'pandas', 'numpy', 'scikit-learn',
            
            # Cloud & DevOps
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'git', 'github',
            'gitlab', 'terraform', 'ansible', 'chef', 'puppet',
            
            # Databases
            'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch', 'oracle',
            'sqlite', 'nosql', 'dynamodb',
            
            # Data & Analytics
            'machine learning', 'data science', 'data analysis', 'business intelligence',
            'tableau', 'power bi', 'excel', 'spark', 'hadoop', 'kafka', 'airflow',
            
            # Soft Skills
            'leadership', 'communication', 'project management', 'problem solving',
            'teamwork', 'collaboration', 'analytical thinking', 'creativity', 'adaptability',
            
            # Methodologies
            'agile', 'scrum', 'kanban', 'waterfall', 'lean', 'devops', 'ci/cd',
            
            # Operating Systems
            'linux', 'windows', 'macos', 'unix', 'ubuntu', 'centos',
            
            # Other Technologies
            'api', 'rest', 'graphql', 'microservices', 'blockchain', 'iot', 'ai',
            'artificial intelligence', 'nlp', 'computer vision', 'cybersecurity'
        }
        
        skills_set.update(predefined_skills)
        
        # Add required skills from constructor
        if self.required_skills:
            skills_set.update([skill.lower() for skill in self.required_skills])
        
        return skills_set

    def extract_skills(self) -> List[str]:
        '''
        Extract skills from resume using section-based approach with comprehensive fallback
        '''
        try:
            all_skills = self._load_skills_database()
            found_skills = set()
            
            # Method 1: Prioritize detected skills section
            skills_text = self.sections.get('skills', '')
            if skills_text:
                logger.info(f"Extracting skills from dedicated section ({len(skills_text)} chars)")
                section_skills = self._extract_from_skills_section(skills_text, all_skills)
                found_skills.update(section_skills)
            
            # Method 2: Extract from other relevant sections (experience, projects)
            for section_name in ['experience', 'projects', 'summary']:
                section_text = self.sections.get(section_name, '')
                if section_text:
                    context_skills = self._extract_skills_from_context(section_text, all_skills)
                    found_skills.update(context_skills)
            
            # Method 3: Match required skills if provided (for backwards compatibility)
            if self.required_skills:
                resume_lower = self.resume_text.lower()
                for skill in self.required_skills:
                    pattern = r"\b" + re.escape(skill.lower()) + r"\b"
                    if re.search(pattern, resume_lower):
                        found_skills.add(skill.lower())
            
            # Method 4: Use spaCy NER for technical entities (if available)
            if self.doc:
                ner_skills = self._extract_skills_using_ner(all_skills)
                found_skills.update(ner_skills)
            
            # Clean and validate results
            validated_skills = self._validate_and_clean_skills(found_skills)
            
            # Return original case for better presentation
            final_skills = self._restore_skill_cases(validated_skills)
            
            logger.info(f"Extracted {len(final_skills)} skills from resume")
            return final_skills
            
        except Exception as e:
            logger.error(f"Error in skills extraction: {e}")
            return []
    
    def _extract_from_skills_section(self, skills_text: str, all_skills: Set[str]) -> Set[str]:
        '''
        Extract skills from dedicated skills section with structured parsing
        '''
        found_skills = set()
        
        # Handle structured skills (like "JavaScript: ReactJS, AngularJS...")
        if self._has_skill_subsections(skills_text):
            structured_skills = self._parse_structured_skills_enhanced(skills_text)
            found_skills.update(structured_skills)
        else:
            # Parse as regular skills list
            section_skills = self._parse_skills_from_section(skills_text)
            found_skills.update(section_skills)
        
        # Also match against known skills database
        skills_text_lower = skills_text.lower()
        for skill in all_skills:
            if len(skill) > 2:  # Skip very short skills
                if ' ' in skill:
                    pattern = r'\b' + re.escape(skill) + r'\b'
                else:
                    pattern = r'\b' + re.escape(skill) + r's?\b'  # Allow plural forms
                
                if re.search(pattern, skills_text_lower, re.IGNORECASE):
                    found_skills.add(skill)
        
        return found_skills
    
    def _extract_skills_from_context(self, context_text: str, all_skills: Set[str]) -> Set[str]:
        '''
        Extract skills mentioned in context (experience, projects, summary)
        '''
        found_skills = set()
        context_lower = context_text.lower()
        
        # Match against known skills with stricter patterns for context
        for skill in all_skills:
            if len(skill) > 3:  # Be more restrictive in context
                pattern = r'\b' + re.escape(skill) + r'\b'
                if re.search(pattern, context_lower, re.IGNORECASE):
                    found_skills.add(skill)
        
        return found_skills
    
    def _extract_skills_using_ner(self, all_skills: Set[str]) -> Set[str]:
        '''
        Extract skills using Named Entity Recognition
        '''
        found_skills = set()
        
        try:
            if self.doc is not None:
                for ent in self.doc.ents:
                    if ent.label_ in ['ORG', 'PRODUCT'] and len(ent.text) > 2:
                        ent_lower = ent.text.lower()
                        # Check if it matches known technology/skill patterns
                        if ent_lower in all_skills:
                            found_skills.add(ent_lower)
        except Exception as e:
            logger.warning(f"Error in NER skills extraction: {e}")
        
        return found_skills
    
    def _parse_structured_skills_enhanced(self, skills_content: str) -> Set[str]:
        '''
        Enhanced parsing of structured skills section (like the sample resume)
        '''
        skills = set()
        lines = skills_content.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if line has category: skills format
            if ':' in line:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    category = parts[0].strip()
                    skills_text = parts[1].strip()
                    
                    # Parse the skills after colon
                    category_skills = self._parse_skills_from_section(skills_text)
                    skills.update(category_skills)
                    
                    # Also add the category if it's a valid skill
                    if category.lower() in ['javascript', 'java', 'python', 'mobile', 'databases']:
                        skills.add(category.lower())
            else:
                # Regular skill line
                line_skills = self._parse_skills_from_section(line)
                skills.update(line_skills)
        
        return skills
    
    def _parse_skills_from_section(self, section_text: str) -> Set[str]:
        '''
        Parse skills from a skills section using various separators
        '''
        skills = set()
        
        # Common separators for skills
        separators = [',', '|', '•', '\u2022', '\n', ';', '/', '\\', '-']
        
        # Replace separators with commas for easier parsing
        cleaned_text = section_text
        for sep in separators:
            cleaned_text = cleaned_text.replace(sep, ',')
        
        # Split and clean
        potential_skills = [skill.strip() for skill in cleaned_text.split(',')]
        
        for skill in potential_skills:
            if 2 < len(skill) < 50 and not skill.isdigit():  # Reasonable length and not just numbers
                # Remove common prefixes/suffixes
                skill = re.sub(r'^[\s\-\•\*]+|[\s\-\•\*]+$', '', skill)
                if skill:
                    skills.add(skill.lower())
        
        return skills
    
    def _validate_and_clean_skills(self, skills: Set[str]) -> List[str]:
        '''
        Validate and clean extracted skills with enhanced filtering for academic resumes
        '''
        valid_skills = []
        
        # Academic/research specific non-skills to filter out
        academic_stopwords = {
            'monisha', 'jegadeesan', 'yulia', 'tsvetkov', 'john', 'wieting', 'sachin', 'kumar',
            'bangalore', 'chennai', 'india', 'madras', 'iit', 'cgpa', 'department', 'college',
            'symposium', 'conference', 'research', 'intern', 'poster', 'paper', 'publication',
            'approach', 'model', 'network', 'transformer', 'bilingual', 'correlation',
            'likelihood', 'employing', 'demonstrated', 'representations', 'structural'
        }
        
        # Month names and common date patterns
        date_patterns = {
            'january', 'february', 'march', 'april', 'may', 'june',
            'july', 'august', 'september', 'october', 'november', 'december',
            'jan', 'feb', 'mar', 'apr', 'may', 'jun',
            'jul', 'aug', 'sep', 'oct', 'nov', 'dec'
        }
        
        for skill in skills:
            # Skip very short or very long skills
            if not (2 < len(skill) < 40):  # Reduced max length
                continue
                
            skill_lower = skill.lower().strip()
            
            # Skip common words that aren't skills
            common_words = {'and', 'the', 'for', 'with', 'are', 'this', 'that', 'have', 'been', 'will', 
                          'allows', 'users', 'create', 'folders', 'upload', 'files', 'metadata',
                          'software', 'engineer', 'engineering', 'computer', 'science', 'technology'}
            if skill_lower in common_words:
                continue
            
            # Skip academic stopwords (names, places, etc.)
            if any(word in skill_lower for word in academic_stopwords):
                continue
                
            # Skip date patterns
            if any(date in skill_lower for date in date_patterns):
                continue
                
            # Skip purely numeric strings or years
            if skill.replace('.', '').replace('-', '').replace('%', '').isdigit():
                continue
                
            # Skip year patterns (1900-2099)
            if re.match(r'^(19|20)\d{2}$', skill.strip()):
                continue
            
            # Skip sentence fragments and bullet points
            if skill.startswith(('●', '•', '-', '+', '*', '[', ']', '(', ')')):
                continue
                
            # Skip if contains brackets, parentheses with text (likely descriptions)
            if re.search(r'[\[\]\(\)].*[a-zA-Z]', skill):
                continue
            
            # Skip if it contains too many common English words (likely a sentence)
            words = skill_lower.split()
            if len(words) > 1:
                common_english_words = {'to', 'of', 'in', 'on', 'at', 'by', 'for', 'with', 'from', 'up', 'about', 'into', 'through', 'during', 'a', 'an', 'the', 'is', 'was', 'are', 'were'}
                common_word_count = sum(1 for word in words if word in common_english_words)
                if common_word_count >= len(words) * 0.25:  # 25% or more common words
                    continue
            
            # Skip incomplete phrases or fragments
            if skill.endswith(('(', ')', ',', '.', ';', ':', 'link', 'code', 'system', 'and', 'or', 'to', 'by', 'with')):
                continue
                
            # Skip if it's all uppercase and too long (likely headers or titles)
            if skill.isupper() and len(skill) > 20:
                continue
                
            # Skip if contains numbers mixed with letters in suspicious ways (likely IDs or codes)
            if re.search(r'\d+[a-zA-Z]+\d+|[a-zA-Z]+\d+[a-zA-Z]+', skill):
                continue
                
            valid_skills.append(skill)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_skills = []
        for skill in valid_skills:
            if skill.lower() not in seen:
                seen.add(skill.lower())
                unique_skills.append(skill)
        
        return unique_skills[:30]  # Limit to top 30 skills for cleaner results
    
    def _restore_skill_cases(self, skills: List[str]) -> List[str]:
        '''
        Restore proper case for skills for better presentation
        '''
        case_mapping = {
            'python': 'Python', 'java': 'Java', 'javascript': 'JavaScript',
            'c++': 'C++', 'c#': 'C#', 'sql': 'SQL', 'html': 'HTML', 'css': 'CSS',
            'aws': 'AWS', 'azure': 'Azure', 'gcp': 'GCP', 'docker': 'Docker',
            'kubernetes': 'Kubernetes', 'react': 'React', 'angular': 'Angular',
            'vue': 'Vue.js', 'node.js': 'Node.js', 'tensorflow': 'TensorFlow',
            'pytorch': 'PyTorch', 'api': 'API', 'rest': 'REST', 'git': 'Git',
            'github': 'GitHub', 'gitlab': 'GitLab', 'ai': 'AI', 'iot': 'IoT',
            'nlp': 'NLP', 'mysql': 'MySQL', 'postgresql': 'PostgreSQL',
            'mongodb': 'MongoDB', 'nosql': 'NoSQL', 'ci/cd': 'CI/CD'
        }
        
        restored_skills = []
        for skill in skills:
            if skill.lower() in case_mapping:
                restored_skills.append(case_mapping[skill.lower()])
            else:
                # Title case for multi-word skills, capitalize for single words
                if ' ' in skill:
                    restored_skills.append(skill.title())
                else:
                    restored_skills.append(skill.capitalize())
        
        return restored_skills

    def extract_education(self) -> List[Dict[str, str]]:
        '''
        Extract structured education from resume sections
        
        Returns:
            List of education dictionaries with degree, institution, year, and additional details
        '''
        try:
            education_entries = []
            
            # Use detected education section if available
            education_text = self.sections.get('education', '')
            
            if not education_text:
                # Fallback to searching entire text
                education_text = self.resume_text
            
            logger.info(f"Extracting education from section of {len(education_text)} characters")
            
            # Parse structured education entries
            structured_education = self._parse_education_entries(education_text)
            
            return structured_education
            
        except Exception as e:
            logger.error(f"Error in education extraction: {e}")
            return []
    
    def _parse_education_entries(self, education_text: str) -> List[Dict[str, str]]:
        '''
        Parse education entries from education section
        '''
        education_entries = []
        lines = education_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or len(line) < 10:  # Skip very short lines
                continue
            
            # Parse education entry
            education_info = self._parse_education_line(line)
            if education_info:
                education_entries.append(education_info)
        
        # If no structured entries found, try pattern matching
        if not education_entries:
            education_entries = self._pattern_match_education(education_text)
        
        return education_entries
    
    def _parse_education_line(self, line: str) -> Dict[str, str]| None:
        '''
        Parse a single education line to extract degree, institution, year, etc.
        
        Examples:
        - "UNIVERSITY OF ARIZONA, Tucson, Arizona"
        - "M.S., Computer Science, 2012"
        - "B.S.B.A., Management Information Systems, 2011"
        '''
        education_info = {}
        
        # Pattern 1: University/Institution with location
        institution_pattern = r'^(UNIVERSITY|COLLEGE|INSTITUTE|SCHOOL)\s+OF\s+([A-Z\s]+),\s*([A-Za-z\s,]+)$'
        match = re.match(institution_pattern, line, re.IGNORECASE)
        if match:
            education_info['institution'] = f"{match.group(1)} OF {match.group(2)}".title()
            education_info['location'] = match.group(3).strip()
            return education_info
        
        # Pattern 2: Degree, Field, Year (like "M.S., Computer Science, 2012")
        degree_field_year_pattern = r'^([A-Z\.\s]+),\s*([A-Za-z\s]+),\s*(\d{4})$'
        match = re.match(degree_field_year_pattern, line)
        if match:
            education_info['degree'] = match.group(1).strip()
            education_info['field'] = match.group(2).strip()
            education_info['year'] = match.group(3).strip()
            return education_info
        
        # Pattern 3: Full education entry (Degree in Field, Institution, Year)
        full_pattern = r'^([A-Z\.\s]+)\s+in\s+([A-Za-z\s]+),\s+([A-Za-z\s]+),\s+(\d{4})'
        match = re.match(full_pattern, line)
        if match:
            education_info['degree'] = match.group(1).strip()
            education_info['field'] = match.group(2).strip()
            education_info['institution'] = match.group(3).strip()
            education_info['year'] = match.group(4).strip()
            return education_info
        
        # Pattern 3b: Bachelor/Master of [Technology] in [Field] [Date Range]
        bachelor_master_pattern = r'^(Bachelor|Master)\s+of\s+(Technology|Science|Arts|Engineering)\s+in\s+([A-Za-z\s]+(?:and\s+[A-Za-z\s]+)?)\s+((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}\s*-\s*(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4})'
        match = re.match(bachelor_master_pattern, line)
        if match:
            education_info['degree'] = f"{match.group(1)} of {match.group(2)}"
            education_info['field'] = match.group(3).strip()
            education_info['duration'] = match.group(4).strip()
            # Extract years from duration
            years = re.findall(r'\d{4}', match.group(4))
            if years:
                education_info['start_year'] = years[0]
                education_info['end_year'] = years[-1] if len(years) > 1 else years[0]
            return education_info
        
        # Pattern 4: Contains degree keywords
        degree_keywords = ['b.s.', 'm.s.', 'b.a.', 'm.a.', 'phd', 'ph.d', 'bachelor', 'master', 
                          'mba', 'diploma', 'certificate', 'b.tech', 'm.tech', 'b.e.', 'm.e.']
        
        if any(keyword in line.lower() for keyword in degree_keywords):
            # Extract components we can identify
            education_info['description'] = line
            
            # Try to extract year
            year_match = re.search(r'(19|20)\d{2}', line)
            if year_match:
                education_info['year'] = year_match.group(0)
            
            # Try to extract degree
            for keyword in degree_keywords:
                if keyword in line.lower():
                    # Find the degree mention and surrounding context
                    start_idx = line.lower().find(keyword)
                    # Look for degree in a reasonable range
                    degree_text = line[max(0, start_idx-10):start_idx+30]
                    education_info['degree'] = degree_text.strip()
                    break
            
            return education_info
        
        # Pattern 5: Institution names
        if any(inst_word in line.lower() for inst_word in ['university', 'college', 'institute', 'school']):
            education_info['institution'] = line
            return education_info
        
        return 
    
    def _pattern_match_education(self, text: str) -> List[Dict[str, str]]:
        '''
        Pattern matching approach for education extraction
        '''
        education_entries = []
        
        # Comprehensive education patterns
        education_patterns = [
            # Full degree with specialization, institution, and year
            r'(?:B\.?(?:Tech|E|Sc|A|Com)|M\.?(?:Tech|E|Sc|A|Com|BA)|Ph\.?D|Bachelor(?:\s+of)?|Master(?:\s+of)?|MBA|Diploma|Certificate)[^,\n.]*?(?:(?:,|\s+at|\s+from|\s+-|\s+\|)\s*[A-Z][^,\n]*(?:University|College|Institute|School))?(?:(?:,|\s+-|\s+\|)\s*(?:19|20)\d{2})?',
            
            # Educational institutions with degrees
            r'(?:University|College|Institute|School)\s+of\s+[A-Z][^,\n]*(?:,\s*(?:B\.|M\.|Ph\.D|Bachelor|Master|MBA)[^,\n]*)?(?:,\s*(?:19|20)\d{2})?',
            
            # GPA patterns
            r'GPA:?\s*\d\.\d+(?:/\d\.\d+)?',
        ]
        
        for pattern in education_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                if match.strip() and len(match.strip()) > 5:
                    education_entries.append({'description': match.strip()})
        
        return education_entries
    
    def extract_experience(self) -> List[Dict[str, str]]:
        '''
        Extract structured experience from resume sections with detailed parsing
        
        Returns:
            List of experience dictionaries with job_title, company, duration, and responsibilities
        '''
        try:
            experiences = []
            
            # Use detected experience section if available
            experience_text = self.sections.get('experience', '')
            if not experience_text:
                # Try research section for academic resumes
                experience_text = self.sections.get('research', '')
            if not experience_text:
                # Fallback to projects section if no experience section
                experience_text = self.sections.get('projects', '')
            
            if not experience_text:
                # Last resort: search entire text
                experience_text = self.resume_text
            
            logger.info(f"Extracting experience from section of {len(experience_text)} characters")
            
            # Parse structured experience entries
            structured_experiences = self._parse_experience_entries(experience_text)
            
            if structured_experiences:
                return structured_experiences
            
            # Fallback to original method for unstructured text
            return self._extract_unstructured_experience(experience_text)
            
        except Exception as e:
            logger.error(f"Error in experience extraction: {e}")
            return []
    
    def _parse_experience_entries(self, experience_text: str) -> List[Dict[str, str]]:
        '''
        Parse structured experience entries from experience section
        '''
        experiences = []
        lines = experience_text.split('\n')
        
        current_experience = {}
        current_responsibilities = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if line is a job header (company, title, dates)
            job_header = self._parse_job_header(line)
            if job_header:
                # Save previous experience if it exists
                if current_experience:
                    current_experience['responsibilities'] = ' '.join(current_responsibilities)
                    experiences.append(current_experience.copy())
                    current_responsibilities = []
                
                current_experience = job_header
                continue
            
            # Check if line is a responsibility/achievement (starts with bullet, dash, or has action verbs)
            if self._is_responsibility_line(line):
                clean_responsibility = self._clean_responsibility_line(line)
                if clean_responsibility:
                    current_responsibilities.append(clean_responsibility)
            
            # Handle multi-line job headers or continuation
            elif current_experience and not current_responsibilities:
                # Might be continuation of job header (location, etc.)
                if self._is_job_detail(line):
                    current_experience['additional_info'] = current_experience.get('additional_info', '') + ' ' + line
        
        # Add the last experience
        if current_experience:
            current_experience['responsibilities'] = ' '.join(current_responsibilities)
            experiences.append(current_experience)
        
        return experiences
    
    def _parse_job_header(self, line: str) -> Dict[str, str] | None:
        '''
        Parse job header line to extract title, company, and dates
        Examples:
        - "WALMART, INC., Bentonville, Arkansas"
        - "Programmer Analyst, Call Center Engineering Team, 2011-2016"
        - "Senior Software Engineer at Google (2021-2023)"
        '''
        job_info = {}
        
        # Pattern 1: Company name followed by location (like WALMART, INC.)
        company_location_pattern = r'^([A-Z][A-Z\s,\.&]+),\s+([A-Za-z\s,]+)$'
        match = re.match(company_location_pattern, line)
        if match:
            job_info['company'] = match.group(1).strip().title()
            job_info['location'] = match.group(2).strip()
            return job_info
        
        # Pattern 2: Title, Team/Department, Dates
        title_team_dates_pattern = r'^([A-Za-z\s]+),\s+([A-Za-z\s]+),\s+(\d{4}[-\s]*\d{4}|\d{4}[-\s]*(?:Present|Current))'
        match = re.match(title_team_dates_pattern, line)
        if match:
            job_info['job_title'] = match.group(1).strip()
            job_info['team'] = match.group(2).strip()
            job_info['duration'] = match.group(3).strip()
            return job_info
        
        # Pattern 3: Title at Company (Dates)
        title_at_company_pattern = r'^(.+?)\s+(?:at|@)\s+(.+?)\s*\((.+?)\)'
        match = re.match(title_at_company_pattern, line)
        if match:
            job_info['job_title'] = match.group(1).strip()
            job_info['company'] = match.group(2).strip()
            job_info['duration'] = match.group(3).strip()
            return job_info
        
        # Pattern 4: Title, Company, Dates (comma-separated)
        comma_separated_pattern = r'^(.+?),\s+(.+?),\s+(\d{4}.*)'
        match = re.match(comma_separated_pattern, line)
        if match:
            job_info['job_title'] = match.group(1).strip()
            job_info['company'] = match.group(2).strip() 
            job_info['duration'] = match.group(3).strip()
            return job_info
        
        # Pattern 5: Handle date ranges at the end of line (like "Nov 2024 - Jan 2025")
        date_at_end_pattern = r'^(.+?)\s+((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}\s*-\s*(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}|Present|Current))$'
        match = re.match(date_at_end_pattern, line)
        if match:
            job_info['job_title'] = match.group(1).strip()
            job_info['duration'] = match.group(2).strip()
            return job_info
        
        # Pattern 5b: Handle academic format like "July 2017 ResearchIntern"
        academic_date_pattern = r'^((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4})\s+(.+)$'
        match = re.match(academic_date_pattern, line)
        if match:
            job_info['duration'] = match.group(1).strip()
            job_info['job_title'] = match.group(2).strip()
            return job_info
        
        # Pattern 6: Handle research-specific formats like "ResearchIntern" or "Research Intern"
        research_pattern = r'^(.+?)\s*(research\s*intern|intern|software\s*engineer|engineer|developer|analyst)\s*(.*)$'
        match = re.match(research_pattern, line, re.IGNORECASE)
        if match:
            prefix = match.group(1).strip()
            job_title = match.group(2).strip()
            suffix = match.group(3).strip()
            
            # If prefix looks like a date, use it as duration
            if re.match(r'^((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}|\d{4})$', prefix, re.IGNORECASE):
                job_info['duration'] = prefix
                job_info['job_title'] = job_title
                if suffix:
                    job_info['additional_info'] = suffix
            else:
                job_info['job_title'] = f"{prefix} {job_title}" if prefix else job_title
                if suffix:
                    job_info['additional_info'] = suffix
            
            return job_info
        
        # Pattern 7: Just check if it contains job-like keywords
        job_keywords = ['engineer', 'developer', 'analyst', 'manager', 'consultant', 'designer', 
                       'scientist', 'specialist', 'coordinator', 'director', 'supervisor', 'intern', 'freelance',
                       'research', 'researcher', 'assistant', 'associate', 'trainee']
        if any(keyword in line.lower() for keyword in job_keywords):
            # Extract what we can
            job_info['job_title'] = line
            
            # Try to extract dates if present
            date_match = re.search(r'(\d{4}[-\s]*\d{4}|\d{4}[-\s]*(?:Present|Current))', line)
            if date_match:
                job_info['duration'] = date_match.group(1)
                job_info['job_title'] = line.replace(date_match.group(1), '').strip()
            
            return job_info
        
        return None
    
    def _is_responsibility_line(self, line: str) -> bool:
        '''
        Check if line represents a responsibility or achievement
        '''
        # Starts with bullet point or dash
        if re.match(r'^\s*[•\*\-▪▫●]', line):
            return True
        
        # Contains action verbs typically used in resumes
        action_verbs = ['architected', 'implemented', 'developed', 'created', 'designed', 'built', 
                       'optimized', 'improved', 'managed', 'led', 'coordinated', 'integrated',
                       'collaborated', 'analyzed', 'researched', 'executed', 'delivered']
        
        line_lower = line.lower()
        if any(verb in line_lower for verb in action_verbs):
            return True
        
        return False
    
    def _clean_responsibility_line(self, line: str) -> str:
        '''
        Clean responsibility line by removing bullets and extra formatting
        '''
        # Remove bullet points and leading/trailing whitespace
        cleaned = re.sub(r'^\s*[•\*\-▪▫●\+]\s*', '', line).strip()
        
        # Remove trailing periods if they don't seem to be abbreviations
        if cleaned.endswith('.') and not re.search(r'\b[A-Z]\.\s*$', cleaned):
            cleaned = cleaned[:-1]
        
        return cleaned
    
    def _is_job_detail(self, line: str) -> bool:
        '''
        Check if line contains additional job details (location, team, etc.)
        '''
        detail_indicators = ['team', 'department', 'division', 'unit', 'group', 'office', 'location']
        return any(indicator in line.lower() for indicator in detail_indicators)
    
    def _extract_unstructured_experience(self, text: str) -> List[Dict[str, str]]:
        '''
        Fallback method for extracting experience from unstructured text
        '''
        experiences = []
        
        # Look for experience-like patterns
        patterns = [
            r'([A-Za-z\s]+(?:Engineer|Developer|Analyst|Manager)[^\n]*(?:\n[^\n]+)*?)(?=\n[A-Z]|$)',
            r'(\d{4}[-\s]*\d{4}[^\n]*(?:\n[^\n]+)*?)(?=\n\d{4}|\n[A-Z]|$)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.MULTILINE)
            for match in matches:
                if len(match.strip()) > 20:  # Minimum meaningful length
                    experiences.append({'description': match.strip()})
        
        return experiences[:5]  # Limit results
    
    def parse(self) -> Dict[str, Any]:
        '''
        Comprehensively parse resume and extract all information with validation
        
        Returns:
            dict: Cleaned and validated resume data with confidence indicators
        '''
        logger.info("Starting comprehensive resume parsing")
        
        try:
            # Extract all information with error handling
            extraction_results = {
                "name": self._safe_extract("name"),
                "email": self._safe_extract("email"), 
                "phone": self._safe_extract("phone"),
                "skills": self._safe_extract("skills"),
                "education": self._safe_extract("education"),
                "experience": self._safe_extract("experience")
            }
            
            # Validate and clean extracted data
            validated_data = self._validate_extracted_data(extraction_results)
            
            # Add metadata
            validated_data["extraction_metadata"] = {
                "resume_length": len(self.resume_text),
                "extraction_timestamp": pd.Timestamp.now().isoformat(),
                "parser_version": "2.0_enhanced",
                "total_fields_extracted": sum(1 for v in validated_data.values() 
                                           if v and v != [] and v != "" and not isinstance(v, dict))
            }
            
            logger.info(f"Successfully parsed resume with {validated_data['extraction_metadata']['total_fields_extracted']} fields")
            return validated_data
            
        except Exception as e:
            logger.error(f"Error in comprehensive parsing: {e}")
            # Return basic structure with error info
            return {
                "name": "",
                "email": "",
                "phone": "",
                "skills": [],
                "education": [],
                "experience": [],
                "extraction_metadata": {
                    "error": str(e),
                    "extraction_timestamp": pd.Timestamp.now().isoformat(),
                    "parser_version": "2.0_enhanced",
                    "total_fields_extracted": 0
                }
            }
    
    def _safe_extract(self, field_name: str):
        '''
        Safely extract a field with error handling
        '''
        try:
            if field_name == "name":
                return self.extract_name()
            elif field_name == "email":
                return self.extract_email()
            elif field_name == "phone":
                return self.extract_phone()
            elif field_name == "skills":
                return self.extract_skills()
            elif field_name == "education":
                return self.extract_education()
            elif field_name == "experience":
                return self.extract_experience()
            else:
                logger.warning(f"Unknown field: {field_name}")
                return None
        except Exception as e:
            logger.error(f"Error extracting {field_name}: {e}")
            # Return appropriate empty value based on expected type
            if field_name in ["skills", "education", "experience"]:
                return []
            else:
                return ""
    
    def _validate_extracted_data(self, data: Dict) -> Dict:
        '''
        Validate and clean all extracted data
        '''
        validated = {}
        
        # Validate name
        name = data.get("name", "")
        validated["name"] = self._clean_name(name) if name else ""
        
        # Validate email
        email = data.get("email", "")
        validated["email"] = self._validate_email(email) if email else ""
        
        # Validate phone
        phone = data.get("phone", "")
        validated["phone"] = self._clean_phone(phone) if phone else ""
        
        # Validate skills (already cleaned in extraction)
        skills = data.get("skills", [])
        validated["skills"] = skills if isinstance(skills, list) else []
        
        # Validate education (now structured)
        education = data.get("education", [])
        if isinstance(education, list) and education:
            if isinstance(education[0], dict):
                # Structured education data
                validated["education"] = education
            else:
                # Legacy string format
                validated["education"] = [self._clean_text(edu) for edu in education if edu and len(edu.strip()) > 5]
        else:
            validated["education"] = []
        
        # Validate experience (now structured)
        experience = data.get("experience", [])
        if isinstance(experience, list) and experience:
            if isinstance(experience[0], dict):
                # Structured experience data
                validated["experience"] = experience
            else:
                # Legacy string format
                validated["experience"] = [self._clean_text(exp) for exp in experience if exp and len(exp.strip()) > 10]
        else:
            validated["experience"] = []
        
        return validated
    
    def _clean_name(self, name: str) -> str:
        '''
        Clean and validate extracted name
        '''
        if not name:
            return ""
            
        # Remove extra whitespace and normalize
        clean_name = re.sub(r'\s+', ' ', name.strip())
        
        # Remove common resume artifacts
        clean_name = re.sub(r'(?i)\b(?:resume|cv|curriculum\s+vitae)\b', '', clean_name)
        
        # Validate it looks like a name (2-4 words, only letters, spaces, common punctuation)
        if re.match(r'^[A-Za-z\s\.\-\']{2,50}$', clean_name) and 2 <= len(clean_name.split()) <= 4:
            return clean_name.title()
        
        return ""
    
    def _validate_email(self, email: str) -> str:
        '''
        Validate extracted email address
        '''
        if not email:
            return ""
            
        # More strict email validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if re.match(email_pattern, email.strip()):
            return email.strip().lower()
        
        return ""
    
    def _clean_phone(self, phone: str) -> str:
        '''
        Clean and normalize phone number
        '''
        if not phone:
            return ""
            
        # Basic cleaning - remove extra spaces
        clean_phone = re.sub(r'\s+', ' ', phone.strip())
        
        # Validate it has reasonable number of digits
        digits = re.sub(r'\D', '', clean_phone)
        if 7 <= len(digits) <= 15:
            return clean_phone
        
        return ""
    
    def _clean_text(self, text: str) -> str:
        '''
        Clean general text fields
        '''
        if not text:
            return ""
            
        # Remove extra whitespace and normalize
        clean_text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove leading/trailing punctuation
        clean_text = re.sub(r'^[\s\-\•\*]+|[\s\-\•\*]+$', '', clean_text)
        
        return clean_text if len(clean_text) > 3 else ""
