import re

def clean_html(raw_html):
    if not raw_html:
        return ""
    text = re.sub('<[^<]+?>', '', raw_html)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def keep_english_only(text):
    lines = text.split('\n')
    english_lines = []
    for line in lines:
        if not line.strip():
            continue
        ascii_ratio = sum(1 for c in line if ord(c) < 128) / max(len(line), 1)
        if ascii_ratio > 0.8:
            english_lines.append(line)
    return '\n'.join(english_lines)

def remove_outcome_phrases(text):
    patterns = [
        r'\b(appeal|petition|writ)\s+(allowed|dismissed|rejected)\b',
        r'\b(we|the court)\s+(allow|dismiss|reject)\b',
        r'\b(is|are)\s+(allowed|dismissed)\b',
        r'\b(conviction|sentence)\s+(upheld|set aside|confirmed)\b',
        r'\b(judgment in favour of|judgment against)\b',
        r'\bLeave\s+Granted\b',
        r'\bLeave\s+granted\b',
        r'\bDisposal\s+Nature\s*:\s*(?:Leave\s+Granted\s*&?\s*)?(?:Allowed|Dismissed)\b',
        r'\bC\.A\.\s+No\.\s+\d+\s+(?:allowed|dismissed)\b',
        r'\b(?:C\.A\.|CIVIL APPEAL)\s+No\.\s+\d+\s+(?:allowed|dismissed)\b'
    ]
    for pat in patterns:
        text = re.sub(pat, '', text, flags=re.IGNORECASE)
    return text

def remove_boilerplate(text):
    text = re.sub(r'English\s*[-–]\s*Hindi\s*[-–]\s*Punjabi.*?(?=\n|$)', '', text, flags=re.DOTALL)
    text = re.sub(r'Disclaimer.*?Ucc', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'Page \d+ of \d+', '', text)
    return text.strip()

def normalise_citations(text):
    text = re.sub(r'\b\d{4}\s+INSC\s+\d+\b', ' CITATION ', text)
    text = re.sub(r'\b\d+\s+SCR\s+\d+\b', ' CITATION ', text)
    text = re.sub(r'\b\d+\s+Supreme\s+Court\s+Cases\s+\d+\b', ' CITATION ', text, flags=re.IGNORECASE)
    return text

def clean_text_comprehensive(text):
    if not text:
        return ""
    text = clean_html(text)
    text = keep_english_only(text)
    text = remove_boilerplate(text)
    text = remove_outcome_phrases(text)
    text = normalise_citations(text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# The raw text you provided (first 500 chars as sample)
raw = """English বাংলা - Bengaliગુજરાતી - Gujaratiहिन्दी - Hindiಕನ್ನಡ - Kannadaമലയാളം - Malayalamमराठी - Marathiਪੰਜਾਬੀ - Punjabiதமிழ் - Tamilతెలుగు - Telugu htam Nyayalya Nirnay Patrika are reproduced under approval of Vidhi Sahitya Prakashan, Department of legislative affairs, Govt. Of India. Supreme Court Registry will not responsible for incorrect or inaccurate translation and for any error, omission or discrepancy in the content of translated text. The translation of Judgements is provided for general information and shall have no legal effect for compliance or enforcement. If any questions arise related to the accuracy of the information/statement contained in the translated judgment, users are advised to verify from the original judgments and also to refer to correct position of law while referring to old judgments. Visitors to the site are requested to cross check the correctness of the information on this site with the authorities concerned or consult the relevant record. The information made available here is not meant for legal evidence. Neither the Courts concerned nor the National Informatics Centre (NIC) nor the e-Committee is responsible for any data inaccuracy or delay in the updation of the data on this website. We do not accept any responsibility or liability for any damage or loss arising from the direct/indirect use of the information provided on the site. However, we shall be obliged if errors/omissions are brought to our notice for carrying out the corrections. STATE OF HARYANA AND ORS. versus RAI CHAND JAIN AND ORS. - [1997] 3 S.C.R. 8941997 INSC 422Coram : K. RAMASWAMY, D.P. WADHWA Seivice Law : Payscales-Parity i11 salary i11 the selectio11 grade payscales-Held : C Since Govemme11t itself has accepted to compute the selection grade wherever available prior to 1.1.86 a11d to work it out 011 the basis of the total strength of the cadre, with co11seque11tial benefits, 110 executive policy, is not violative of ATt, J4-Co11stitutio11 of India, Art, 14. D Teachers who have not acquired higher qualificatio11s-Held not en- titled to higher payscales. State of Harylllla &amp; A11r. v. Ravi Bala &amp; Ors., (1997) 1 SCC 267 and Wazir Singh v. State of Haryana, (1995) Decision Date : 21-04-1997 | Case No : CIVIL APPEAL No. 3236/1997 | Disposal Nature : Leave Granted & Allowed | Direction Issue : C.A. No. 3236 to 3266 and 3268 to 3274/97 dismissed. C.A. No. 3267/97 allowed. | Bench : 2 JudgesFlip viewPDF"""

cleaned = clean_text_comprehensive(raw)
print("CLEANED TEXT:")
print(cleaned)
print("\nLength:", len(cleaned))