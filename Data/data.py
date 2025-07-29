import json
import support
import requests
import spimage

with open("real_data/apidata.txt", encoding="utf-8") as f:
    api_data = json.loads(f.read())

with open("real_data/sourcedata.txt", encoding="utf-8") as f:
    source_data = json.loads(f.read())

def QuesFilter(questions:list, startques=1):
    ret = []
    listyp = []
    QuestionFiltered = None
    for question in questions:
        print(startques, end=" - ")
        questyp = question.get("question_type")
        if question.get("description"): #question đại diện lưu mô tả
            if QuestionFiltered:
                ret.append(QuestionFiltered)
            typ = support.MappingQType.get_typeinlist(questyp)
            if typ not in listyp: listyp.append(typ)
            listques = []
            if questyp in ["MAP_DIAGRAM_LABEL", "FILL_BLANK"] or \
                (questyp == "OTHERS" and question.get("type") == "FILL-IN-THE-BLANK"):
                if questyp == "OTHERS": questyp = "FILL_BLANK"
                is_gap_fill = True
                title, description, descKey = support.LocDesc(question.get("description"))
                if not description: 
                    description = support.LocDesc(question.get("title"))[1]
                instruction = {
                    "title": title,
                    "description": description
                }
                if questyp == "MAP_DIAGRAM_LABEL":
                    instruction["imagesDescription"] = "https://dx4zn9s1ngor1.cloudfront.net/public/reading/1753737128408_2244.png"
                if descKey: instruction["descriptionKey"] = descKey
                ict, listques = support.GapfilltoJson(question.get("gap_fill_in_blank"),question.get("explain"), question.get("title"))
                startques = int(listques[-1].get("id")) + 1
                if ict.get("instruction"): instruction.update(ict["instruction"])

            elif questyp == "MULTIPLE_CHOICE_MANY":
                is_gap_fill = True
                lques, startques = support.MulChoiceMany(question, startques)
                listques = [lques]
                instruction = support.InsTFandYN(question.get("description"))
            else: 
                is_gap_fill = False
                instruction = support.InsTFandYN(question.get("description"))
            if not instruction.get("title"):
                instruction["title"] = "Questions"
            if not instruction.get("description"):
                instruction["description"] = "1111"
            QuestionFiltered = {
                "displayType": support.MappingQType.get_displaytype(questyp),
                "questionType": support.MappingQType.get_questiontype(questyp),
                "instruction": instruction,
                "questions":listques
            }
            if questyp in ["MAP_DIAGRAM_LABEL", "FILL_BLANK"]: 
                QuestionFiltered["content"] = ict.get("content")
                if ict.get("title"):    
                    QuestionFiltered["title"] = ict.get("title")
                    
            if is_gap_fill: 
                continue

        if questyp == "MULTIPLE_CHOICE_ONE":
                cont = support.MulChoiceOne(question.get("single_choice_radio",[]))
        ques ={
            "id": str(startques),
            "text": question.get("selection")[0].get("text") if not question.get("single_choice_radio") else question.get("title"),
            "options": cont["options"] if question.get("single_choice_radio") else [opt.get("option") for opt in question.get("selection_option", [])],
            "correctAnswer": cont["correctAnswer"] if question.get("single_choice_radio") else question.get("selection")[0].get("answer"),
            "explanation": support.Decode(question.get("explain"))
        }
        QuestionFiltered["questions"].append(ques)
        startques += 1
    if QuestionFiltered:  # Thêm QuestionFiltered cuối cùng
        ret.append(QuestionFiltered)
    return ret, listyp, startques

def getSource(data, id):
    dt = data["data"]
    ret = []
    for item in dt.get("items", []):
        if item.get("id") == id:
            for tag in item.get("tags", []):
                if tag["code"] in ["CAM", "RECENT_TESTS", "RL-FORECAST", "TRAINER"]:
                    ret.append(tag.get("title"))
    return ret[0] if len(ret) else None

def filter_json(data, source_data):
    requiredData = data["data"]
    list_part = []
    listTypQues = []
    parts = []
    startques = 1
    for part in requiredData.get("parts", []):
        list_part.append(part.get("passage"))
        qParts, listyp, startques = QuesFilter(part.get("questions",[]), startques)
        listTypQues += [typ for typ in listyp if typ not in listTypQues]
        content, listpassIns, title = support.Content(support.Decode(part.get("content")))
        title = requiredData.get("title")
        PassageFiltered ={
            "passageIndex": part.get("passage"),
            "passageInstruction": part.get("instruction"),
            "passageTitle": title if title else part.get("title"),
            "passageContent": content,
            "questionParts": qParts
        }
        if listpassIns:
            PassageFiltered["passageInstruction"] = "{(\n)}".join(listpassIns)
        parts.append(PassageFiltered)
    source = getSource(source_data, requiredData["id"])
    readingTestFiltered = {
        "testType": f'Passage {list_part[0]}' if len(list_part) == 1 else "Full Reading Test",
        "image": "https://dx4zn9s1ngor1.cloudfront.net/public/reading/1752744128408_6833.png",
        "testTitle": requiredData.get("title"),
        "questionTypeInTest": listTypQues,
        "parts": parts,
        "source": source
    } 
    return readingTestFiltered, requiredData.get("thumbnail")

data, keyurl = filter_json(api_data, source_data)

with open("real_data/output.txt", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

# print(keyurl)
    
##############################################################
#Upload    
##############################################################    

api_url = "http://127.0.0.1:8080/api/admin-reading/reading-tests/"

if keyurl is None:
    files = {"data": (None, json.dumps(data), "application/json")}
else:
    img_url = f"https://cms.youpass.vn/assets/{keyurl}"
    files = spimage.XuliImg(img_url)
    files["data"] = (None, json.dumps(data), "application/json")

response = requests.post(api_url, files=files)

# Kiểm tra phản hồi
if response.status_code == 201:
    print("Upload thành công:")
    with open("real_data/statusoutput.txt", "w", encoding="utf-8") as f:
        json.dump(response.json(), f, ensure_ascii=False, indent=2)
else:
    print("Upload thất bại:", response.status_code)
    with open("real_data/statusoutput.txt", "w", encoding="utf-8") as f:
        json.dump(response.text, f, ensure_ascii=False, indent=2)
