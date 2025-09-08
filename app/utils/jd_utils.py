import re
from datetime import datetime
from typing import List, Dict, Optional
from app.lib.skills_lib import SKILLS

class JDParser:
    """
    Lightweight text parser that can operate on either Job Descriptions (JD) or Resumes.
    It extracts skills, education signals, and experience years using robust regex patterns
    and simple heuristics without external heavy NLP dependencies.

    Return types are kept compatible with existing usage:
    - extract_skills -> list[str]
    - extract_education -> list[str]
    - extract_experience -> {"min": int|float, "max": int|float|None} | None
    """

    def __init__(self, jd_text: str):
        # Normalize spacing but preserve original for potential future needs
        self.original_text = jd_text
        self.text = self._normalize(jd_text)
        self.skills_catalog = [s.strip() for s in SKILLS if isinstance(s, str) and s.strip()]

    @staticmethod
    def _normalize(text: str) -> str:
        # Lowercase, normalize separators, and collapse whitespace
        t = text.lower()
        # Replace common separators with spaces to help word-boundary matching
        t = re.sub(r"[\u2013\u2014\-/\\|]+", " ", t)  # en dash/em dash/slash/pipe
        t = re.sub(r"[()\[\],;]", " ", t)
        t = re.sub(r"\s+", " ", t).strip()
        return t

    def extract_skills(self) -> List[str]:
        """
        Extract skills by matching against the curated SKILLS list with robust boundaries.
        Handles punctuation (e.g., C++, Node.js), multi-word terms, and separators.
        """
        found: List[str] = []
        text = self.text

        # Pre-compute a safe searchable text with dots removed only when surrounded by letters
        # but keep word boundaries via regex below
        for skill in self.skills_catalog:
            skill_norm = skill.lower().strip()
            if not skill_norm:
                continue
            # Build a boundary-aware pattern that allows dots and pluses inside tokens
            # e.g., "node.js", "c++", "react native"
            token = re.escape(skill_norm)
            token = token.replace(r"\+", r"\+")  # keep + literal
            # Allow optional dots inside words: react\.js -> react\.?js
            token = re.sub(r"\\\.(\w)", r"\\\.?\1", token)
            pattern = rf"(?<![a-z0-9]){token}(?![a-z0-9])"
            if re.search(pattern, text, flags=re.I):
                found.append(skill)

        # Deduplicate while preserving original casing from SKILLS
        return sorted(list({s: None for s in found}.keys()), key=lambda x: x.lower())

    def extract_experience(self) -> Optional[Dict[str, float]]:
        """
        Extract years of experience from a wide variety of formats.
        Supports:
        - "3 years", "3+ years", "3-5 years", "5 – 7 yrs", "at least 5 years"
        - Months: "6 months" (converted to 0.5 years)
        - Aggregation of multiple mentions; also attempts to infer total from date ranges
          like "Jan 2020 – Mar 2023", "2019-2021", "2018 – Present".
        Returns a dict with min/max when ranges are present, else only min (total approx.).
        """
        text = self.text
        years: List[float] = []
        ranges: List[tuple[float, float]] = []

        # 1) Explicit year ranges and single values
        for m in re.finditer(r"(\d+)(?:\s*[-–]\s*(\d+))?\s*\+?\s*(?:years?|yrs?)", text, flags=re.I):
            a = float(m.group(1))
            b = float(m.group(2)) if m.group(2) else None
            if b is not None:
                ranges.append((min(a, b), max(a, b)))
            else:
                years.append(a)

        # 2) Months mentions
        for m in re.finditer(r"(\d+)\s*\+?\s*(?:months?|mos?)", text, flags=re.I):
            months = float(m.group(1))
            years.append(round(months / 12.0, 2))

        # 3) Phrases like "at least 5 years", "minimum 3 years"
        for m in re.finditer(r"(?:at\s+least|min(?:imum)?)\s*(\d+)\s*(?:years?|yrs?)", text, flags=re.I):
            years.append(float(m.group(1)))

        # 4) Try to infer total experience from date ranges in resumes
        inferred_years = self._infer_years_from_date_ranges(text)
        if inferred_years:
            years.append(inferred_years)

        # Aggregate results
        min_val: Optional[float] = None
        max_val: Optional[float] = None

        if ranges:
            min_val = min(r[0] for r in ranges)
            max_val = max(r[1] for r in ranges)

        if years:
            total = sum(years)
            # If no explicit ranges, treat sum as a minimum approximation
            if min_val is None:
                min_val = total
            else:
                # If we have both, keep the larger min
                min_val = max(min_val, total)

        if min_val is None and max_val is None:
            return None

        # Round to one decimal place for readability
        result: Dict[str, float] = {"min": round(min_val, 2) if min_val is not None else 0.0}
        if max_val is not None:
            result["max"] = round(max_val, 1)
        return result

    def _infer_years_from_date_ranges(self, text: str) -> float:
        """Infer total years from resume-like date ranges.
        Very heuristic: looks for patterns like "Jan 2020 – Mar 2023", "2019-2021", "2018 – Present".
        """
        # Month abbreviations
        months = {
            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
            'jul': 7, 'aug': 8, 'sep': 9, 'sept': 9, 'oct': 10, 'nov': 11, 'dec': 12
        }
        now = datetime.utcnow()
        total_months = 0

        # Pattern A: Month Year – Month Year / Present
        pattern_a = re.compile(
            r"(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)\s+(\d{4})\s*[–-]\s*("
            r"(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)\s+(\d{4})|present)",
            flags=re.I,
        )
        for m in pattern_a.finditer(text):
            sm, sy, tail = m.group(1), m.group(2), m.group(3)
            start_month = months[sm.lower()]
            start_year = int(sy)
            if tail.lower() == "present":
                end_year, end_month = now.year, now.month
            else:
                em, ey = m.group(4), m.group(5)
                end_month = months[em.lower()]
                end_year = int(ey)
            total_months += max(0, (end_year - start_year) * 12 + (end_month - start_month))

        # Pattern B: Year – Year
        pattern_b = re.compile(r"(\d{4})\s*[–-]\s*(\d{4}|present)", flags=re.I)
        for m in pattern_b.finditer(text):
            sy = int(m.group(1))
            tail = m.group(2).lower()
            if tail == "present":
                ey = now.year
            else:
                ey = int(tail)
            # Assume mid-year if months not provided
            total_months += max(0, (ey - sy) * 12)

        return round(total_months / 12.0, 1) if total_months > 0 else 0.0

    def extract_education(self) -> List[str]:
        """
        Extract education levels and common degree variants present in resumes and JDs.
        Examples handled: bachelor's/bachelors, master's/masters, b.tech/b.e, m.tech/m.e,
        bsc/msc, diploma, associate, mba, mca, bca, phd/doctorate, bs/ms.
        Returns a list of normalized labels (not raw spans) to remain compatible downstream.
        """
        patterns: Dict[str, str] = {
            "bachelor": r"\bbachelor(?:'s)?\b|\bbs\b|\bb\.?sc\b|\bb\.?e\b|\bb\.?tech\b|\bbca\b",
            "master": r"\bmaster(?:'s)?\b|\bms\b|\bm\.?sc\b|\bm\.?e\b|\bm\.?tech\b|\bmba\b|\bmca\b",
            "phd": r"\bph\.?d\.?\b|\bdoctorate\b",
            "associate": r"\bassociate\b",
            "diploma": r"\bdiploma\b",
            "degree": r"\bdegree\b",
        }
        found: List[str] = []
        for label, pat in patterns.items():
            if re.search(pat, self.text, flags=re.I):
                found.append(label)
        return sorted(list({s: None for s in found}.keys()))

    def parse(self) -> dict:
        """
        Combines all functions to extract information.
        """
        result = {
            "skills": self.extract_skills(),
            "education": self.extract_education(),
            "experience": self.extract_experience(),
        }
        return result
