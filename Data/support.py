import re
import html
import json
import string
from bs4 import BeautifulSoup


def Content(data):
    data = re.sub(r'\{\[', ' ', data, flags=re.IGNORECASE)
    data = re.sub(r'\]\[(.+?)\]\}', ' ', data, flags=re.IGNORECASE)
    return data

def Decode(data):
    data = re.sub(r'YouPass', 'Youready', data, flags=re.IGNORECASE)
    return html.unescape(data)

def mapIdDesciption(contents: str):
    decoded = Decode(contents)
    
    decoded = re.sub(r'Câu\s*\d+\s*:</div>', '', decoded, flags=re.IGNORECASE)
    matches = re.findall(r'\{\[(.+?)\]\[(\d+)\]\}', decoded,  flags=re.DOTALL)
    tuplemap = {id: content for content, id in matches}
    return tuplemap, decoded

def LocText(data:str, flag=False):
    soup = BeautifulSoup(data, 'html.parser')
    if flag:
        for h3 in soup.find_all('h3'):
            h3.decompose()
    text = ''
    for element in soup.children:
        if element.name == 'p':
            element_text = element.get_text().strip()
            if element_text:
                text += element_text + '\n'
        elif element.name == 'ul':
            for ele in element.children:
                element_text = ele.get_text().strip()
                if element_text:
                    text += "● " + element_text + '\n'
        elif element.name:
            element_text = element.get_text().strip()
            if element_text:
                text += element_text
        else:
            element_text = str(element).strip()
            if element_text:
                text += element_text
    text = re.sub(r'\n\s*\n', '\n', text.strip())
    text = re.sub(r'\n', '{(\n)}', text.strip())
    return text

def GapfilltoJson(gap_fill_in_blank: str, explain: str, strmaxword):
    number_map = {
        'ONE': 1,
        'TWO': 2,
        'THREE': 3,
        'FOUR': 4,
        'FIVE': 5,
        'SIX': 6,
        'SEVEN': 7,
        'EIGHT': 8,
        'NINE': 9,
        'TEN': 10
    }
    regex = r'\b(ONE|TWO|THREE|FOUR|FIVE|SIX|SEVEN|EIGHT|NINE|TEN)\s+WORD(S)?\b'
    matches = re.findall(regex, strmaxword, re.IGNORECASE)
    
    if not matches:
        maxword = 1
    else:    
        number_word = matches[0][0].upper()
        maxword = number_map.get(number_word)
    correct_answer, decoded = mapIdDesciption(gap_fill_in_blank)
    explains,_ = mapIdDesciption(explain)  
    soup = BeautifulSoup(decoded, 'html.parser')
    title = soup.find('h3').get_text(strip=True) if soup.find('h3') else None
    text = LocText(decoded, True)
    content = re.sub(r'\{\[(.+?)\]\[(\d+)\]\}', "{(input)}", text)
    questions = [{"id": idx,"maxWord": maxword, "correctAnswer": word, "explanation": explains.get(idx,"")} for idx, word in correct_answer.items()]

    return content, title, questions

def InsTFtoJson(data:str):
    decoded = Decode(data)
    soup = BeautifulSoup(decoded, 'html.parser')

    # Title 
    title = soup.find('h2').get_text(strip=True)

    # Description
    desc_paras = []
    # Key descriptions
    desc_key = {}
    # print("==== DECODED HTML ====")
    # print(decoded)
    for p in soup.find_all('p'):
        # print("=== RAW P ===  ", p)
        text = p.get_text(strip=True).strip()
        if p.find_parent(['td', 'table']):
            # print("TABLE  ", p)
            az_pattern = re.compile(r"^[A-Za-z]+$")
            for strong_tag in p.find_all('strong'):
                key_text = strong_tag.get_text(strip=True)
                # key_text = re.sub(r'\s+', '', key_text)
                # print(key_text)
                if az_pattern.match(key_text):
                    value = ""
                    if strong_tag.next_sibling:
                        value = strong_tag.next_sibling.strip()
                    desc_key[key_text] = value
            continue
        if text and any(keyword in text.upper() for keyword in ["TRUE", "FALSE", "YES", "NO", "NOT GIVEN"]):
            break  
        desc_paras.append(p)
    
    descriptions = ["<p>" + p.decode_contents()+ "</p>" for p in desc_paras if p]

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
        "description": LocText("".join(descriptions)),
        "descriptionKey": desc_key
    } if desc_key else {
        "title": title,
        "description": LocText("".join(descriptions))
    } 

def MulChoiceMany(data: str, startques):
    list_opt = []
    list_correct = []
    list_explain = []
    text = data.get("title")
    data = data.get("mutilple_choice",[])
    for option in data:
        list_opt.append(Decode(option["text"]))
        list_correct.append(option["correct"])
        if option.get("explain"): list_explain.append(Decode(option["explain"]))

    opts = [f"{label}. {opt.lstrip()}" for label, opt in zip(string.ascii_uppercase, list_opt)]
    lcorrect = [opt for opt,f in zip(string.ascii_uppercase,list_correct) if f]
    num = len(lcorrect)
    startques += num
    return {
        "id": f"{startques-num}-{startques-1}",
        "text": text,
        "options": opts,
        "correctAnswer": lcorrect,
        "explanation": list_explain
    }, startques

def MulChoiceOne(data: str):
    list_opt = []
    list_correct = []
    for option in data:
        list_opt.append(Decode(option["text"]))
        list_correct.append(option["correct"])
    opts = [f"{label}. {opt.lstrip()}" for label, opt in zip(string.ascii_uppercase, list_opt)]
    lcorrect = [opt for opt,f in zip(opts,list_correct) if f]
    return {
        "options": opts,
        "correctAnswer": lcorrect[0],
    }

# with open("real_data/explain.txt", encoding="utf-8") as f:
#     explain = f.read()

# with open("real_data/gapfillinblank.txt", encoding="utf-8") as f:
#     gap_fill_in_blank = f.read()
    
# jsonstr = GapfilltoJson(gap_fill_in_blank,explain)
# print(json.dumps(jsonstr, ensure_ascii=False, indent=2))


class MappingQType:
    mapping = {
        "MATCHING_HEADING": ("Matching Heading", "MATCHING_HEADING", "MATCHING"),
        "MATCHING_INFO": ("Matching Information", "MATCHING_INFO", "MATCHING"),
        "FILL_BLANK": ("Gap Filling", "FILL_BLANK", "GAP_FILLING"),
        "MULTIPLE_CHOICE_MANY": ("Multiple Choice (Many Answer)", "MULTIPLE_CHOICE_MANY", "MULTIPLE_SELECTION"),
        "MULTIPLE_CHOICE_ONE": ("Multiple Choice (One Answer)", "MULTIPLE_CHOICE_ONE", "SINGLE_SELECTION"),
        "YES_NO": ("Yes - No - Not Given", "YES_NO_NOT_GIVEN", "SINGLE_SELECTION"),
        "MATCHING_NAMES": ("Matching Names", "MATCHING_NAMES", "SINGLE_SELECTION"),
        "TRUE_FALSE": ("True - False - Not Given", "TRUE_FALSE_NOT_GIVEN", "SINGLE_SELECTION")
    }

    @classmethod
    def get_typeinlist(cls, key):

        return cls.mapping.get(key)[0]

    @classmethod
    def get_questiontype(cls, key):
        return cls.mapping.get(key)[1]

    @classmethod
    def get_displaytype(cls, key):
        return cls.mapping.get(key)[2]