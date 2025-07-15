import re
import html
import json
import string
from bs4 import BeautifulSoup, NavigableString


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
    title, text, desc_key = LocDesc(decoded)
    content = re.sub(r'\{\[(.+?)\]\[(\d+)\]\}', "{(input)}", text)
    questions = [{"id": idx,"maxWord": maxword, "correctAnswer": word, "explanation": explains.get(idx,"")} for idx, word in correct_answer.items()]
    
    ret = {"content": content}
    if desc_key: ret["instruction"] = {"descriptionKey": desc_key}
    if title: ret["title"] = title
    return ret, questions

def TFandYN(text: str):
    desc_key = {}
    for keyword in ["TRUE", "FALSE", "YES", "NOT GIVEN", "NOTGIVEN", "NO"]:
        if keyword in text and len(text.split(keyword)) > 1:
            key_word = "NOT GIVEN" if keyword == "NOTGIVEN" else keyword
            desc_key[key_word] = text.split(keyword)[1].strip()
            break
    return bool(desc_key), desc_key

def LocDesc(data):
    soup = BeautifulSoup(data, 'html.parser') if isinstance(data, str) else data
    text = []
    title = "Question :"
    flag = False
    desckey = {}

    def process_element(element, depth=0):
        nonlocal title, text, flag, desckey
        if isinstance(element, NavigableString):
            element_text = str(element).strip()
            if element_text:
                if flag and text:
                    text[-1] += ' ' + element_text
                    flag = False
                else:
                    text.append(element_text)
            return
        if element.name in ["h2", "h3"]:
            title = element.get_text(strip=True)
        elif element.name in ["div", "p"]:
            if text: text[-1] += '\n'
            flag = False
            fla, descKey = TFandYN(element.get_text(strip=True))
            if fla:
                desckey.update(descKey)
            for child in element.children:
                process_element(child, depth + 1)
        elif element.name == "ul":
            for child in element.children:
                if child.name == "li":
                    element_text = child.get_text().strip()
                    if element_text:
                        text.append("● " + element_text)
        elif element.name == "br":
            text.append("\n")
        elif element.name == "table":
            for p in soup.find_all(['p','div']):
                if p.find_parent(['td', 'table']):
                    az_pattern = re.compile(r"^[A-Za-z]+\.?$")
                    for strong_tag in p.find_all('strong'):
                        key_text = strong_tag.get_text(strip=True)
                        if az_pattern.match(key_text):
                            value = ""
                            if strong_tag.next_sibling:
                                value = strong_tag.next_sibling.strip()
                            desckey[key_text] = value
            if desckey: return
            for p in soup.find_all(['td']):
                if p.find_parent('table'):
                    az_pattern = re.compile(r"^[A-Za-z]+\.?$")
                    for strong_tag in p.find_all('strong'):
                        key_text = strong_tag.get_text(strip=True)
                        if az_pattern.match(key_text):
                            value = ""
                            if strong_tag.next_sibling:
                                value = strong_tag.next_sibling.strip()
                            desckey[key_text] = value
        elif element.name:
            element_text = element.get_text().strip()
            if element_text:
                if text:
                    text[-1] += ' ' + element_text
                    flag = True
                else:
                    text.append(element_text)

    for element in soup.children:
        process_element(element)

    text = "\n".join(t for t in text if t).strip()
    text = re.sub(r'\n\s*\n', '\n', text)
    text = re.sub(r'\n', '{(\n)}', text)
    text = re.sub(r' \.', '.', text)
    text = re.sub(r' \,', ',', text)
    if "TRUE if" in text:
        text = text.split("{(\n)} TRUE if")[0].strip()
    elif "YES if" in text:
        text = text.split("{(\n)} YES if")[0].strip()
    return title, text, desckey

def InsTFandYN(data: str):
    title, descriptions, desc_key = LocDesc(data)
    ret  = {
        "title": title,
        "description": descriptions,
    }
    if desc_key: ret["descriptionKey"] = desc_key
    return ret  

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
    lcorrect = [opt for opt,f in zip(string.ascii_uppercase,list_correct) if f]
    return {
        "options": opts,
        "correctAnswer": lcorrect[0],
    }

class MappingQType:
    mapping = {
        "MATCHING_HEADING": ("Matching Heading", "MATCHING_HEADING", "MATCHING"),
        "MATCHING_INFO": ("Matching Information", "MATCHING_INFO", "MATCHING"),
        "FILL_BLANK": ("Gap Filling", "FILL_BLANK", "GAP_FILLING"),
        "MULTIPLE_CHOICE_MANY": ("Multiple Choice (Many Answer)", "MULTIPLE_CHOICE_MANY", "MULTIPLE_SELECTION"),
        "MULTIPLE_CHOICE_ONE": ("Multiple Choice (One Answer)", "MULTIPLE_CHOICE_ONE", "SINGLE_SELECTION"),
        "YES_NO": ("Yes - No - Not Given", "YES_NO_NOT_GIVEN", "SINGLE_SELECTION"),
        "MATCHING_NAMES": ("Matching Names", "MATCHING_NAMES", "SINGLE_SELECTION"),
        "TRUE_FALSE": ("True - False - Not Given", "TRUE_FALSE_NOT_GIVEN", "SINGLE_SELECTION"),
        "OTHERS": ("Other Types", "MATCHING_NAMES", "SINGLE_SELECTION"),
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
    

# with open("real_data/apidata.txt", encoding="utf-8") as f:
#     desc = f.read()
   
# title, des, deskey = LocDesc(desc)
# data = {
#     "title": title,
#     "description": des,
#     "descriptionKey": deskey
# }

# with open("real_data/output.txt", "w", encoding="utf-8") as f:
#     json.dump(data, f, ensure_ascii=False, indent=2)
