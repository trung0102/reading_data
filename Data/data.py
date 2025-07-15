import json
import support
import requests
import spimage

with open("real_data/apidata.txt", encoding="utf-8") as f:
    api_data = json.loads(f.read())

def QuesFilter(questions:list, startques=1):
    ret = []
    listyp = []
    QuestionFiltered = None
    for question in questions:
        # print(startques)
        if question.get("description"): #question đại diện lưu mô tả
            if QuestionFiltered:
                ret.append(QuestionFiltered)
            typ = support.MappingQType.get_typeinlist(question.get("question_type"))
            if typ not in listyp: listyp.append(typ)
            listques = []
            if question.get("question_type") == "FILL_BLANK":
                is_gap_fill = True
                instruction = {
                    "title": support.LocDesc(question.get("description"))[0],
                    "description": support.LocDesc(question.get("title"))[1]
                }
                ict, listques = support.GapfilltoJson(question.get("gap_fill_in_blank"),question.get("explain"), question.get("title"))
                startques = int(listques[-1].get("id")) + 1
                if ict.get("instruction"): instruction.update(ict["instruction"])
            elif question.get("question_type") == "MULTIPLE_CHOICE_MANY":
                is_gap_fill = True
                lques, startques = support.MulChoiceMany(question, startques)
                listques = [lques]
                instruction = support.InsTFandYN(question.get("description"))
            else: 
                is_gap_fill = False
                instruction = support.InsTFandYN(question.get("description"))
            QuestionFiltered = {
                "displayType": support.MappingQType.get_displaytype(question.get("question_type")),
                "questionType": support.MappingQType.get_questiontype(question.get("question_type")),
                "instruction": instruction,
                "questions":listques
            }
            if question.get("question_type") == "FILL_BLANK": 
                QuestionFiltered["content"] = ict.get("content")
                if ict.get("title"):    
                    QuestionFiltered["title"] = ict.get("title")
            if is_gap_fill: 
                continue

        if question.get("question_type") == "MULTIPLE_CHOICE_ONE":
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

def filter_json(data):
    requiredData = data["data"]
    list_part = []
    listTypQues = []
    parts = []
    startques = 1
    for part in requiredData.get("parts", []):
        list_part.append(part.get("passage"))
        qParts, listyp, startques = QuesFilter(part.get("questions",[]), startques)
        listTypQues += [typ for typ in listyp if typ not in listTypQues]
        PassageFiltered ={
            "passageIndex": part.get("passage"),
            "passageInstruction": part.get("instruction"),
            "passageTitle": part.get("title"),
            "passageContent": support.Content(support.Decode(part.get("content"))),
            "questionParts": qParts
        }
        parts.append(PassageFiltered)

    readingTestFiltered = {
        "testType": f'Passage {list_part[0]}' if len(list_part) == 1 else "Full Reading Test",
        "image": "readingtest.png",
        "testTitle": requiredData.get("title"),
        "questionTypeInTest": listTypQues,
        "parts": parts
    } 
    return readingTestFiltered, requiredData.get("thumbnail")

data, keyurl = filter_json(api_data)

with open("real_data/output.txt", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

# print(keyurl)
api_url = "http://127.0.0.1:8000/api/admin-reading/reading-tests/"

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
