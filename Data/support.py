import re
import html
import json
from bs4 import BeautifulSoup


def Decode(data):
    data = re.sub(r'YouPass', '', data, flags=re.IGNORECASE)
    return html.unescape(data)

def mapIdDesciption(contents: str):
    decoded = Decode(contents)
    
    decoded = re.sub(r'Câu\s*\d+\s*:</div>', '', decoded, flags=re.IGNORECASE)
    matches = re.findall(r'\{\[(.+?)\]\[(\d+)\]\}', decoded,  flags=re.DOTALL)
    tuplemap = {id: content for content, id in matches}
    return tuplemap, decoded

def GapfilltoJson(gap_fill_in_blank: str, explain: str, maxword=1):
    if maxword == 0: maxword = 1
    correct_answer, decoded = mapIdDesciption(gap_fill_in_blank)
    explains,_ = mapIdDesciption(explain)
    content = re.sub(r'\{\[(.+?)\]\[(\d+)\]\}', lambda m: f'{{{{{m.group(2)}}}}}', decoded)

    questions = [{"id": idx,"maxWord": maxword, "correctAnswer": word, "explanation": explains.get(idx,"")} for idx, word in correct_answer.items()]

    return content, questions

def InsTFtoJson(data:str):
    decoded = Decode(data)
    soup = BeautifulSoup(decoded, 'html.parser')

    # Title
    title = soup.find('h2').get_text(strip=True)

    # Description
    desc_paras = []
    for p in soup.find_all('p'):
        text = p.get_text(strip=True).strip()
        if text and any(keyword in text.upper() for keyword in ["TRUE", "FALSE", "YES", "NO", "NOT GIVEN"]):
            break  
        desc_paras.append(p)
    
    descriptions = [p.decode_contents() for p in desc_paras if p]

    # Key descriptions
    desc_key = {}
    for p in soup.find_all('p'):
        text = p.get_text(" ", strip=True)
        if 'TRUE' in text:
            desc_key["TRUE"] = text.split("TRUE")[1].strip()
        elif 'FALSE' in text:
            desc_key["FALSE"] = text.split("FALSE")[1].strip()
        elif 'YES' in text:
            desc_key["YES"] = text.split("YES")[1].strip()
        elif 'NOT GIVEN' in text:
            desc_key["NOT GIVEN"] = text.split("NOT GIVEN")[1].strip()
        elif 'NO' in text:
            desc_key["NO"] = text.split("NO")[1].strip() if "NO" in text else text

    return {
        "title": title,
        "description": "\n".join(descriptions),
        "descriptionKey": desc_key
    }

with open("real_data/explain.txt", encoding="utf-8") as f:
    explain = f.read()

with open("real_data/gapfillinblank.txt", encoding="utf-8") as f:
    gap_fill_in_blank = f.read()
    
# jsonstr = GapfilltoJson(gap_fill_in_blank,explain)
# print(json.dumps(jsonstr, ensure_ascii=False, indent=2))

    