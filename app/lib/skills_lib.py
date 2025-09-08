import pandas as pd
from pathlib import Path

# Try to load skills from Excel file first, fallback to CSV
try:
    xlsx_path = Path("app/utils/skills_dataset.xlsx")
    if xlsx_path.exists():
        df = pd.read_excel(xlsx_path)
        print(f"Loaded skills from Excel: {df.shape[0]} rows, columns: {df.columns.tolist()}")
    else:
        # Fallback to CSV
        df = pd.read_csv("app/job_skills.csv")  
        print(f"Loaded skills from CSV: {df.shape[0]} rows")
except Exception as e:
    print(f"Error loading skills database: {e}")
    # Create empty dataframe as fallback
    df = pd.DataFrame({'Skills': []})

# Handle different possible column names
skill_column = None
for col in df.columns:
    if any(keyword in col.lower() for keyword in ['skill', 'technology', 'tool']):
        skill_column = col
        break

if skill_column is None:
    # Try common names
    common_names = ['Skills', 'Skill', 'Technology', 'Technologies']
    for name in common_names:
        if name in df.columns:
            skill_column = name
            break

if skill_column and skill_column in df.columns:
    SKILL_STACK = (df[skill_column].str.split(","))
    SKILL_SUBSETS = [skillset for skillset in SKILL_STACK if skillset is not None] 
    SKILLS = [skill.lower().strip() for skill_SUBSET in SKILL_SUBSETS for skill in skill_SUBSET if skill and skill.strip()]
else:
    print("Warning: No suitable skills column found in database")
    SKILLS = []
