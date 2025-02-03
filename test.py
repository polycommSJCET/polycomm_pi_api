import ast

def convert_string_to_list(s):
    try:
        return ast.literal_eval(s)
    except (SyntaxError, ValueError):
        raise ValueError("Invalid input string format")

# Example usage
s = """[(1, 2, [3, (4, 5)]), (6, [7, (8, 9)])]"""
result = convert_string_to_list(s)
print(result)