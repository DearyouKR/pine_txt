import json


with open("data/value_all.json", "r") as file:
    value_all = json.load(file)


print(len(value_all))

pine_data = {}

for key, value in value_all.items():
    # print(key, value)
    l_add = 0
    l_minus = 0

    s_add = 0
    s_minus = 0

    pine_data[key] = {}
    dj_value = 0.8 * 0.8
    length = 12

    for symbol, symbol_value in value.items():
        if "_l" in symbol and symbol_value >= dj_value:
            l_add += 1

        if l_add >= length:
            pine_data[key].update({"l_add": l_add})

        if "_l" in symbol and symbol_value <= -dj_value:
            l_minus += 1

        if l_minus >= length:
            pine_data[key].update({"l_minus": l_minus})


        if "_s" in symbol and symbol_value >= dj_value:
            s_add += 1

        if s_add >= length:
            pine_data[key].update({"s_add": s_add})

        if "_s" in symbol and symbol_value <= -dj_value:
            s_minus += 1

        if s_minus >= length:
            pine_data[key].update({"s_minus": s_minus})


add_list = []
minus_list = []

for t, data in pine_data.items():
    for key, value in data.items():
        if "l_add" in key:
            add_list.append(f"     time == {int(float(t))} ? 'ladd_{value}' : ")

        if "s_add" in key:
            add_list.append(f"     time == {int(float(t))} ? 'sadd_{value}' : ")

        if "l_minus" in key:
            minus_list.append(f"     time == {int(float(t))} ? 'lminus_{value}' : ")

        if "s_minus" in key:
            minus_list.append(f"     time == {int(float(t))} ? 'sminus_{value}' : ")


# print("add:\n\n")
# for txt in add_list:
#     print(txt)
#
# print("\n\nminus:\n\n")
# for txt in minus_list:
#     print(txt)


with open("../pine_dict.json", "r") as file:
    pine_dict = json.load(file)

# 添加新的键值对
pine_dict["add"] = add_list
pine_dict["minus"] = minus_list

# 保存更新后的数据
with open("../pine_dict.json", "w") as file:
    json.dump(pine_dict, file, indent=4)
