# import spacy
import re

# Load English tokenizer, tagger, parser and NER
# nlp = spacy.load("en_core_web_sm")

class ResumeParser :

    def __init__(self,resume_text,required_skills:list[str]=None):
        self.resume_text = resume_text 
        self.doc = nlp(resume_text)
        self.required_skills = required_skills if required_skills else []

    def extract_name(self)->str:

        '''
        Extract name from resume_text
        '''

        doc = nlp(self.resume_text)

        # extract first line
        first_line = self.resume_text.strip().split('\n')[0].strip()
    
        # If the first line has >1 word, assume it's the name
        if len(first_line.split())> 1 :
            name = first_line
            return name
    
        else:
            for ent in doc.ents :
        
               if ent.label_ == 'PERSON' :
                  name = ent.text
                  return name
        return ""

    def extract_phone(self)->str:
        '''
        Extract phone number from resume_text

        examples : 
        9861289352

        +91 9861289352

        123-456-7890

        (123) 456 7890
        '''
        phone_regex = r"\+?\d[\d\s\-]{7,}\d"
        phone = re.search(phone_regex,self.resume_text)
        return phone.group() if phone else ""
    
    def extract_email(self)->str:
        '''
        Extract email from resume_text
        '''
        email_regex = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
        email = re.findall(email_regex,self.resume_text)[0]
        return email if email else ""
    
    def extract_skills(self)->list[str]:
        '''
        Extract skills from a resume text.
    
        Returns:
            str: Extracted text list.
        '''
        matched_skills = []
        resume_text = self.resume_text.lower()

        for skill in self.required_skills : 
            pattern = r"\b" + re.escape(skill.lower()) + r"\b"
            if(re.search(pattern, resume_text)):
                matched_skills.append(skill)

        return list(set(matched_skills))

    def extract_education(self)->list[str]:
        '''
        Extracts education from resume_text
        
        examples : 

        B.Tech in Computer Science, IIT Delhi, 2021

        MBA, Harvard Business School, 2019

        Bachelor of Science in Physics, 2020

        '''

        education_regex = r"""
        (?:
            (?:B\.?Tech|M\.?Tech|B\.?Sc|M\.?Sc|B\.?E|M\.?E|
            MBA|Ph\.?D|Bachelor|Master|Diploma|Associate)
            [^,\n]*                # specialization (like Computer Science)
            (?:,?\s*(?:University|College|Institute|School)[^,\n]*)?   # institution
            (?:,?\s*\d{4})?        # graduation year
        )
        """

        education = re.findall(education_regex,self.resume_text,re.VERBOSE)

        return [edu.strip() for edu in education ]
    
    def extract_experience(self)->list[str]:
        '''
        Extract experience from resume_text

        examples:

        Software Engineer at Google (2021-2023)

        Data Analyst, Microsoft, 2019-2021

        Intern, Infosys, 6 months

        Project Manager at TCS, 2015-2018
        
        '''

        experience_regex = r"""
        (?:
            (?:Intern|Software Engineer|Developer|Manager|Consultant|Analyst|
            Designer|Data Scientist|Researcher|Lead|Engineer)
            [^,\n]*                       # role details
            (?:at\s+[A-Z][A-Za-z0-9& ]+)? # optional "at Company"
            (?:\s*\(?\d{4}\s*-\s*\d{4}\)?)?   # years in (2020-2022)
            (?:\s*\(?\d+\+?\s*(?:months?|years?)\)?)? # or "2 years"
        )
        """

        experiences = re.findall(experience_regex,self.resume_text,re.VERBOSE)
        return experiences
    
    def parse(self)->dict:
        '''
        combines all functions to extract all information from resume

        returns :

          dict
        '''
        resume_dict = {
            "name" : self.extract_name(),
            "email" : self.extract_email(),
            "phone" : self.extract_phone(),
            "skills" : self.extract_skills(),
            "education" : self.extract_education(),
            "experience" : self.extract_experience(),
            # "raw text" : self.resume_text
        }

        return resume_dict