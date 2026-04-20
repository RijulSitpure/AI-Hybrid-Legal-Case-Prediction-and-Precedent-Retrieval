import re

raw = """English বাংলা - Bengaliગુજરાતી - Gujaratiहिन्दी - Hindiಕನ್ನಡ - Kannadaമലയാളം - Malayalamमराठी - Marathiਪੰਜਾਬੀ - Punjabiதமிழ் - Tamilతెలుగు - Telugu htam Nyayalya Nirnay Patrika are reproduced under approval of Vidhi Sahitya Prakashan, Department of legislative affairs, Govt. Of India. Supreme Court Registry will not responsible for incorrect or inaccurate translation and for any error, omission or discrepancy in the content of translated text. The translation of Judgements is provided for general information and shall have no legal effect for compliance or enforcement. If any questions arise related to the accuracy of the information/statement contained in the translated judgment, users are advised to verify from the original judgments and also to refer to correct position of law while referring to old judgments. Visitors to the site are requested to cross check the correctness of the information on this site with the authorities concerned or consult the relevant record. The information made available here is not meant for legal evidence. Neither the Courts concerned nor the National Informatics Centre (NIC) nor the e-Committee is responsible for any data inaccuracy or delay in the updation of the data on this website. We do not accept any responsibility or liability for any damage or loss arising from the direct/indirect use of the information provided on the site. However, we shall be obliged if errors/omissions are brought to our notice for carrying out the corrections. STATE OF HARYANA AND ORS. versus RAI CHAND JAIN AND ORS. - [1997] 3 S.C.R. 8941997 INSC 422Coram : K. RAMASWAMY, D.P. WADHWA Seivice Law : Payscales-Parity i11 salary i11 the selectio11 grade payscales-Held : C Since Govemme11t itself has accepted to compute the selection grade wherever available prior to 1.1.86 a11d to work it out 011 the basis of the total strength of the cadre, with co11seque11tial benefits, 110 executive policy, is not violative of ATt, J4-Co11stitutio11 of India, Art, 14. D Teachers who have not acquired higher qualificatio11s-Held not en- titled to higher payscales. State of Harylllla &amp; A11r. v. Ravi Bala &amp; Ors., (1997) 1 SCC 267 and Wazir Singh v. State of Haryana, (1995) Decision Date : 21-04-1997 | Case No : CIVIL APPEAL No. 3236/1997 | Disposal Nature : Leave Granted & Allowed | Direction Issue : C.A. No. 3236 to 3266 and 3268 to 3274/97 dismissed. C.A. No. 3267/97 allowed. | Bench : 2 JudgesFlip viewPDF"""

# Remove HTML tags
text = re.sub('<[^<]+?>', '', raw)
# Remove non-ASCII (keep only English)
text = re.sub(r'[^\x00-\x7F]+', ' ', text)
# Find the case title start (uppercase with "versus")
match = re.search(r'(STATE OF .*?versus .*?\.)', text)
if match:
    start_idx = match.start()
    text = text[start_idx:]
# Remove everything after "Decision Date"
text = re.sub(r'Decision Date\s*:.*$', '', text, flags=re.DOTALL)
# Remove outcome phrases
text = re.sub(r'Disposal Nature\s*:\s*[^|]+\|?', '', text)
text = re.sub(r'Direction Issue\s*:.*', '', text)
text = re.sub(r'C\.A\.\s+No\.\s+\d+\s+(?:allowed|dismissed)', '', text, flags=re.IGNORECASE)
# Remove extra whitespace
text = re.sub(r'\s+', ' ', text).strip()
print(text)