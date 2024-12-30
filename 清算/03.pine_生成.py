import json
import pprint

with open("data/value_all.json", "r") as file:
    value_all = json.load(file)


print(len(value_all))
pine_data = {}

for key, value in value_all.items():
    # print(key, value)
    l_value = 0
    s_value = 0
    pine_data[key] = {}


    dj_value = 0.7
    length = 12

    for symbol, symbol_value in value.items():
        if "_l" in symbol and symbol_value >= dj_value:
            l_value += 1

        if l_value >= length:
            pine_data[key].update({"l": l_value})

        if "_s" in symbol and symbol_value >= dj_value:
            s_value += 1
        if s_value >= length:
            pine_data[key].update({"s": s_value})

# pprint.pprint(pine_data)

l_pine_txt_list = []
s_pine_txt_list = []

for key, value in pine_data.items():
    if "l" in value:
        l_pine_txt_list.append(f"     time == {int(float(key) * 1000)} ? 'L_{value['l']}' : ")

for key, value in pine_data.items():
    if "s" in value:
        s_pine_txt_list.append(f"     time == {int(float(key) * 1000)} ? 'S_{value['s']}' : ")


# print("l:\n\n")
# for txt in l_pine_txt_list:
#     print(txt)
#
#
# print("\n\ns:\n\n")
# for txt in s_pine_txt_list:
#     print(txt)
#
with open("../pine_dict.json", "r") as file:
    pine_dict = json.load(file)

# 添加新的键值对
pine_dict["L"] = l_pine_txt_list
pine_dict["S"] = s_pine_txt_list

# 保存更新后的数据
with open("../pine_dict.json", "w") as file:
    json.dump(pine_dict, file, indent=4)
