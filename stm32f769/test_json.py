import json

with open("todo.json", "r") as f:
    data = f.read()

template = json.loads(data)
print(template)
