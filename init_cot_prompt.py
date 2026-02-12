
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_main.settings")
django.setup()

from django_qa.models import PromptTemplate

def init_cot_prompt():
    scene = "cot_programming"
    if PromptTemplate.objects.filter(scene=scene).exists():
        print(f"Prompt for {scene} already exists.")
        return

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
    print(f"Created CoT prompt for {scene}.")

if __name__ == "__main__":
    init_cot_prompt()
