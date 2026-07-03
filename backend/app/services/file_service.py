"""
File Service: 文件解析与提取服务
支持 PDF/MD/TXT 文件上传 → 文本提取 → 复用 NoteService 入库
"""
from pathlib import Path
from .note_service import note_service


class FileService:
    """文件解析服务（全局单例，仿 note_service 模式）"""

    SUPPORTED_EXTENSIONS = {".pdf", ".md", ".txt"}

    async def extract_text(self, file_content: bytes, filename: str) -> str:
        """根据文件扩展名路由到对应的解析器"""
        ext = Path(filename).suffix.lower()
        if ext not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(f"不支持的文件类型: {ext}（支持: {', '.join(sorted(self.SUPPORTED_EXTENSIONS))}）")

        if ext == ".pdf":
            return await self._parse_pdf(file_content)
        elif ext in (".md", ".txt"):
            return file_content.decode("utf-8", errors="replace")

        return file_content.decode("utf-8", errors="replace")

    async def _parse_pdf(self, content: bytes) -> str:
        """使用 PyMuPDF (fitz) 提取 PDF 文本"""
        try:
            import fitz
        except ImportError:
            raise RuntimeError(
                "PyMuPDF 未安装，无法解析 PDF 文件。\n"
                "请运行: pip install pymupdf"
            )

        text_parts = []
        try:
            doc = fitz.open(stream=content, filetype="pdf")
            for page in doc:
                page_text = page.get_text()
                if page_text.strip():
                    text_parts.append(page_text)
            doc.close()
        except Exception as e:
            raise RuntimeError(f"PDF 解析失败: {e}")

        if not text_parts:
            raise RuntimeError("PDF 文件中未提取到文本内容（可能是扫描件或图片型 PDF）")

        return "\n\n".join(text_parts)

    async def process_upload(
        self,
        file_content: bytes,
        filename: str,
        title: str = None,
        user_id: str = "default",
    ) -> dict:
        """
        完整上传链路: 解析文本 → 调用 NoteService.save_note 入库

        返回: 保存后的 note dict
        """
        # Step 1: 提取文本
        text = await self.extract_text(file_content, filename)

        if not text or not text.strip():
            raise RuntimeError(f"文件 '{filename}' 内容为空，无法入库")

        # Step 2: 确定标题
        title = title or Path(filename).stem

        # Step 3: 复用 NoteService 完整持久化链路
        return await note_service.save_note(
            title=title,
            content_md=text,
            summary="",
            tags=[],
            user_id=user_id,
            source_type="uploaded",
            embed=True,
        )


# 全局单例
file_service = FileService()
