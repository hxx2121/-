
import os
import django
import sys

# Add project root to sys.path
sys.path.append(os.getcwd())

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_main.settings")
try:
    django.setup()
    print("Django setup success")
except Exception as e:
    print(f"Django setup failed: {e}")
    sys.exit(1)

from django_qa.models import PromptTemplate
from django_qa.utils.code_analysis import analyze_code_comprehensive

def check_system():
    # 1. Check CoT Prompt
    scene = "cot_programming"
    exists = PromptTemplate.objects.filter(scene=scene).exists()
    print(f"CoT Prompt '{scene}' exists: {exists}")
    
    if not exists:
        print("Creating CoT prompt...")
        system_prompt = """你是一个精通编程的大模型助手。
请使用思维链（Chain of Thought）方法来解决用户的编程问题。
在给出最终代码或答案之前，请先详细分析问题的需求、潜在的边界情况、算法选择的理由以及代码结构的设计。

请按照以下步骤思考：
1. **问题分析**：理解用户的核心需求和输入输出约束。
2. **逻辑设计**：规划解决问题的算法或架构，解释为什么选择这个方案（对比其他方案）。
3. **代码实现**：提供完整的、经过注释的代码。
4. **验证与优化**：检查潜在的 bug，分析时间/空间复杂度，并提出优化建议。

请确保代码符合最佳实践，语法正确，且易于阅读。"""

        user_prompt_template = """用户问题：
{{question}}

上下文信息：
{{context}}

请开始你的思维链推理："""

        PromptTemplate.objects.create(
            scene=scene,
            version="v1_cot",
            system_prompt=system_prompt,
            user_prompt_template=user_prompt_template,
            is_active=True
        )
        print("CoT prompt created.")

    # 2. Check Code Analysis
    code_sample = """
def hello(name):
    print(f"Hello, {name}")
    return True
"""
    result = analyze_code_comprehensive(code_sample)
    print("Code Analysis Result Keys:", list(result.keys()))
    print("Result:", result)
    
    expected_keys = ['syntax_score', 'logic_score', 'utility_score', 'readability_score', 'total_score', 'report']
    missing = [k for k in expected_keys if k not in result]
    if missing:
        print(f"FAILED: Missing keys in code analysis: {missing}")
    else:
        print("SUCCESS: Code analysis returns all 4 dimensions.")

if __name__ == "__main__":
    check_system()
