def replace_specific_placeholder(template, placeholder_key, value):
    """
    替换指定的占位符为给定的值

    :param template: 包含占位符的模板字符串
    :param placeholder_key: 要替换的占位符键（不含{{}}）
    :param value: 替换占位符的值
    :return: 替换后的字符串
    """
    placeholder = f"{{{{{placeholder_key}}}}}"  # 构建占位符格式，例如 {{short_key}}
    return template.replace(placeholder, str(value))

# 示例模板
template = "这是一个模板，其中包含占位符：{{long_key}} 和 {{short_key}}。"

# 要替换的占位符和值
placeholder_key = "short_key"
value = 111

# 替换占位符
result = replace_specific_placeholder(template, placeholder_key, value)

print(result)
