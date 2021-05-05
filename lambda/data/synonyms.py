import json
s_json = open('synonyms.json', 'r')
data = json.load(s_json)

print(data['slots']['ward']['resolutions']['resolutionsPerAuthority'][0]['values'][0]['value']['name'])