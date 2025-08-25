import re
# from lib.skills_lib import SKILLS

class JDParser:

    def __init__(self,jd_text:str):
        self.jd_text = jd_text.lower()
        self.skills = []
   
    def extract_skills(self)-> list[str]:
        found = []

        for skill in self.skills :
            if re.search(rf"\b{re.escape(skill.lower())}\b", self.jd_text):
                found.append(skill)

        return list(set(found))
    
    def extract_experience(self) -> dict | None:
        """
        Extracts years of experience. Handles cases like:
        - "3 years"
        - "3+ years"
        - "3-5 years"
        - "5–7 yrs"
        """
        match = re.search(
            r'(\d+)(?:\s*[-–]\s*(\d+))?\s*\+?\s*(?:years?|yrs?)',
            self.jd_text
        )
        if match:
            return {
                "min": int(match.group(1)),
                "max": int(match.group(2)) if match.group(2) else None
            }
        return None

    def extract_education(self) -> list[str]:
        """
        Extracts education levels. Handles variations like:
        - bachelor's, bachelors
        - master's, masters
        - Ph.D., PhD
        - doctorate
        """
        edu_levels = {
            "bachelor": r"\bbachelor(?:'s)?\b",
            "master": r"\bmaster(?:'s)?\b",
            "phd": r"\bph\.?d\.?\b|\bdoctorate\b",
            "degree": r"\bdegree\b"
        }
        found = []
        for level, pattern in edu_levels.items():
            if re.search(pattern, self.jd_text):
                found.append(level)
        return found
    
    def parse(self)-> dict:
        '''
        combines all functions to extract all information from jd

        returns :
          dict
        '''
        resume_dict = {
            "skills" : self.extract_skills(),
            "education" : self.extract_education(),
            "experience" : self.extract_experience(),
            # "raw text" : self.resume_text
        }

        return resume_dict