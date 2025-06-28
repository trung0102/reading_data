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
        if question.get("description"): #question đại diện lưu mô tả
            if QuestionFiltered:
                ret.append(QuestionFiltered)
            listyp.append(question.get("question_type"))
            if question.get("gap_fill_in_blank"):
                is_gap_fill = True
                instruction = {
                    "title": question.get("description"),
                    "description": question.get("title")
                }
                content, listques = support.GapfilltoJson(question.get("gap_fill_in_blank"),question.get("explain"), question.get("max_words"))
            else: 
                is_gap_fill = False
                instruction = support.InsTFtoJson(question.get("description"))
            QuestionFiltered = {
                "displayType": question.get("type"),
                "questionType": question.get("question_type"),
                "instruction": instruction,
                "content": content if is_gap_fill else None,
                "questions":listques if is_gap_fill else []
            }
            if is_gap_fill: continue
        
        ques ={
            "id": str(startques),
            "text": question.get("selection")[0].get("text"),
            "options": [opt.get("option") for opt in question.get("selection_option", [])],
            "correctAnswer": question.get("selection")[0].get("answer"),
            "explanation": support.Decode(question.get("explain"))
        }
        QuestionFiltered["questions"].append(ques)
        startques += 1
    if QuestionFiltered:  # Thêm QuestionFiltered cuối cùng
        ret.append(QuestionFiltered)
    return ret, listyp

def filter_json(data):
    requiredData = data["data"]
    list_part = []
    listTypQues = []
    parts = []
    for part in requiredData.get("parts", []):
        list_part.append(part.get("passage"))
        qParts, listyp = QuesFilter(part.get("questions",[]))
        listTypQues += listyp
        PassageFiltered ={
            "passageIndex": part.get("passage"),
            "passageInstruction": part.get("instruction"),
            "passageTitle": part.get("title"),
            "passageContent": support.Decode(part.get("content")),
            "questionParts": qParts
        }
        parts.append(PassageFiltered)

    readingTestFiltered = {
        "testType": f'Passage {list_part[0]}' if len(list_part) == 1 else "Full Reading Test",
        "image": "abc.png",
        "testTitle": requiredData.get("title"),
        "questionTypeInTest": listTypQues,
        "parts": parts
    } 
    return readingTestFiltered, requiredData.get("thumbnail")

data, keyurl = filter_json(api_data)

with open("real_data/output.txt", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

# print(keyurl)


#xử lí ảnh và gửi request vào api
# img_url = "https://cms.youpass.vn/assets/" + keyurl
    
# api_url = "http://127.0.0.1:8000/api/admin-reading/reading-tests/"
# files = spimage.XuliImg(img_url)
# files["data"] = (None, json.dumps(data), "application/json")

# print(files)

# response = requests.post(api_url, files=files)

# # Kiểm tra phản hồi
# if response.status_code == 200:
#     print("Upload thành công:")
#     with open("real_data/statusoutput.txt", "w", encoding="utf-8") as f:
#         json.dump(response.json(), f, ensure_ascii=False, indent=2)
# else:
#     print("Upload thất bại:", response.status_code)
#     with open("real_data/statusoutput.txt", "w", encoding="utf-8") as f:
#         json.dump(response.text, f, ensure_ascii=False, indent=2)
