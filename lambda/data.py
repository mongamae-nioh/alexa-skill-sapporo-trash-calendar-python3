# data
import json
trash_json = open('./data/trashdata.json', 'r')
trash_data = json.load(trash_json)

print(trash_data['trash_number']['燃やせる'])