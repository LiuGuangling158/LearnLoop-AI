"""
文本分块工具
支持 Markdown 按标题层级切分 + token 级别控制
"""
import re
from ..core.config import settings


def split_markdown_by_headers(
    text: str,
    chunk_size: int = None,
    chunk_overlap: int = None,
) -> list[dict]:
    """
    按 Markdown 标题 (H1-H3) 切分文本

    返回: [
        {
            "content": "分块内容...",
            "section_path": "H1标题 > H2标题",
            "chunk_index": 0,
            "token_count": 150,
        },
        ...
    ]
    """
    chunk_size = chunk_size or settings.chunk_size
    chunk_overlap = chunk_overlap or settings.chunk_overlap

    # 按标题拆分
    sections = re.split(r'(?=^#{1,3}\s)', text, flags=re.MULTILINE)
    sections = [s.strip() for s in sections if s.strip()]

    if not sections:
        sections = [text]

    chunks = []
    current_section_path = ""

    for i, section in enumerate(sections):
        # 提取标题
        header_match = re.match(r'^(#{1,3})\s+(.+)', section)
        if header_match:
            level = len(header_match.group(1))
            title = header_match.group(2).strip()
            # 更新 section_path
            if level == 1:
                current_section_path = title
            elif level == 2:
                parts = current_section_path.split(" > ")
                current_section_path = " > ".join(parts[:1] + [title])
            else:
                parts = current_section_path.split(" > ")
                current_section_path = " > ".join(parts[:2] + [title])

        # 如果段落太长，进一步切分
        if len(section) > chunk_size:
            sub_chunks = _split_long_section(section, chunk_size, chunk_overlap)
            for j, sub in enumerate(sub_chunks):
                chunks.append({
                    "content": sub,
                    "section_path": current_section_path,
                    "chunk_index": len(chunks),
                    "token_count": _estimate_tokens(sub),
                })
        else:
            chunks.append({
                "content": section,
                "section_path": current_section_path,
                "chunk_index": len(chunks),
                "token_count": _estimate_tokens(section),
            })

    return chunks


def _split_long_section(text: str, chunk_size: int, overlap: int) -> list[str]:
    """将长段落按字符数切分，保留重叠"""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap
    return chunks


def _estimate_tokens(text: str) -> int:
    """粗略估算 token 数量：中文约 1 字 = 1 token，英文约 1 词 = 1.3 token"""
    chinese_chars = len(re.findall(r'[一-鿿]', text))
    english_words = len(re.findall(r'[a-zA-Z]+', text))
    return chinese_chars + int(english_words * 1.3)
