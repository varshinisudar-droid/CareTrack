import re


def extract_medical_information(text):
    """
    Extract basic medical information from OCR text.
    Prototype only — not clinical diagnosis.
    """

    if not text:
        return {
            "medications": [],
            "dates": [],
            "symptoms": [],
            "medical_terms": []
        }

    # -----------------------------
    # Dates
    # -----------------------------
    dates = re.findall(
        r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
        text
    )

    # -----------------------------
    # Medication patterns
    # -----------------------------
    medication_pattern = (
        r"\b[A-Z][A-Za-z-]{2,}"
        r"(?:\s+\d+\s*(?:mg|ml|mcg|g))?\b"
    )

    possible_medications = re.findall(
        medication_pattern,
        text
    )

    # -----------------------------
    # Symptoms
    # -----------------------------
    symptom_keywords = [
        "pain",
        "fever",
        "cough",
        "headache",
        "nausea",
        "vomiting",
        "fatigue",
        "dizziness",
        "swelling",
        "cold",
        "breathlessness"
    ]

    lower_text = text.lower()

    symptoms = [
        symptom
        for symptom in symptom_keywords
        if symptom in lower_text
    ]

    # -----------------------------
    # Medical terms
    # -----------------------------
    medical_keywords = [
        "diagnosis",
        "prescription",
        "blood pressure",
        "diabetes",
        "infection",
        "treatment",
        "tablet",
        "capsule",
        "dosage",
        "follow-up"
    ]

    medical_terms = [
        term
        for term in medical_keywords
        if term in lower_text
    ]

    return {
        "medications": possible_medications[:20],
        "dates": dates,
        "symptoms": symptoms,
        "medical_terms": medical_terms
    }
