from __future__ import annotations

import ast
import html
import re
import tempfile
import subprocess
import os

def _extract_code_blocks(text: str) -> list[str]:
    if not text:
        return []
    out: list[str] = []

    fenced = re.findall(r"```(?:python|py)?\s*([\s\S]*?)```", text, flags=re.IGNORECASE)
    out.extend([b.strip() for b in fenced if b and b.strip()])

    html_blocks = re.findall(r"<pre><code>([\s\S]*?)</code></pre>", text, flags=re.IGNORECASE)
    for b in html_blocks:
        s = html.unescape(b or "")
        s = re.sub(r"<[^>]+>", "", s)
        s = s.replace("\r\n", "\n").replace("\r", "\n").strip()
        if s:
            out.append(s)

    lines = (text or "").replace("\r\n", "\n").replace("\r", "\n").splitlines()
    buf: list[str] = []
    for line in lines + [""]:
        is_code = line.startswith("    ") or line.startswith("\t")
        if is_code:
            buf.append(line[4:] if line.startswith("    ") else line[1:])
            continue
        if buf:
            block = "\n".join(buf).strip()
            if block:
                out.append(block)
            buf = []

    deduped: list[str] = []
    seen: set[str] = set()
    for b in out:
        key = b.strip()
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(b)
    return deduped

def _run_pylint(code: str) -> float:
    """运行Pylint分析代码质量，返回0-10分的评分"""
    if not code:
        return 4.0
    
    # 创建临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        f.write(code)
        temp_file = f.name
    
    try:
        # 运行Pylint，禁用文档字符串检查，使用文本报告
        cmd = [
            'pylint',
            '--disable=C0111',  # 禁用缺少文档字符串警告
            '--disable=C0116',  # 禁用缺少函数文档字符串警告
            '--output-format=text',
            temp_file
        ]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10  # 防止超时
        )
        
        # 提取评分（Pylint输出格式：Your code has been rated at X.X/10）
        score_match = re.search(r'rated at ([0-9.]+)/10', result.stdout)
        if score_match:
            return float(score_match.group(1))
        return 4.0  # 默认分数
    except Exception:
        return 4.0  # 异常时返回默认分数
    finally:
        # 清理临时文件
        if os.path.exists(temp_file):
            try:
                os.unlink(temp_file)
            except:
                pass

def analyze_code_comprehensive(text: str) -> dict:
    code_blocks = _extract_code_blocks(text)
    
    # 1. 语法正确性（AST解析）
    syntax_score = 10.0
    if code_blocks:
        ok = 0
        for b in code_blocks:
            try:
                ast.parse(b)
                ok += 1
            except Exception:
                pass
        syntax_score = 10.0 * (ok / len(code_blocks)) if code_blocks else 10.0
    
    # 2. 易读性（Pylint评分）
    readability_score = 4.0
    if code_blocks:
        pylint_scores = []
        for b in code_blocks:
            pylint_scores.append(_run_pylint(b))
        readability_score = sum(pylint_scores) / len(pylint_scores) if pylint_scores else 4.0
    
    # 3. 逻辑完整性（基于易读性变换）
    logic_score = min(10.0, readability_score * 0.9 + 1.0)
    
    # 4. 通用性（启发式规则）
    utility_score = 4.0
    if code_blocks:
        for b in code_blocks:
            # 检测函数定义
            if re.search(r'def\s+\w+\s*\(', b):
                utility_score += 2.0
            # 检测类定义
            if re.search(r'class\s+\w+', b):
                utility_score += 2.0
            # 检测导入语句
            if re.search(r'import\s+|from\s+\w+\s+import', b):
                utility_score += 1.0
            # 检测异常处理
            if re.search(r'try:\s*|except\s+', b):
                utility_score += 1.0
        utility_score = min(10.0, utility_score)
    
    # 加权融合计算综合评分
    total_score = (
        syntax_score * 0.25 +  # 语法25%
        logic_score * 0.30 +    # 逻辑30%
        utility_score * 0.20 +   # 通用性20%
        readability_score * 0.25 # 易读性25%
    )
    total_score = min(10.0, max(0.0, total_score))
    
    report = " | ".join(
        [
            f"syntax={syntax_score:.1f}",
            f"logic={logic_score:.1f}",
            f"utility={utility_score:.1f}",
            f"readability={readability_score:.1f}",
            f"total={total_score:.1f}"
        ]
    )

    return {
        "syntax_score": syntax_score,
        "logic_score": logic_score,
        "utility_score": utility_score,
        "readability_score": readability_score,
        "total_score": total_score,
        "report": report,
    }
