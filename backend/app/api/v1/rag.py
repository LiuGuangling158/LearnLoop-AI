"""
RAG 知识检索 API 路由
"""
from fastapi import APIRouter, HTTPException, UploadFile, File
from ...core.orchestrator import orchestrator
from ...utils.schemas import RAGAskRequest

router = APIRouter(prefix="/rag", tags=["知识检索"])


@router.post("/ask")
async def ask_knowledge(request: RAGAskRequest):
    """
    知识库问答
    """
    agent = orchestrator.get_agent("retrieval_agent")
    if not agent:
        raise HTTPException(status_code=500, detail="Retrieval Agent 未注册")

    result = await agent.execute(
        context=orchestrator._context,
        user_input=request.query,
        query=request.query,
        top_k=request.top_k,
    )

    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)

    return {
        "success": True,
        "data": result.data,
        "metadata": result.metadata,
    }


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    上传文档到知识库
    支持 .md / .txt / .pdf
    """
    # TODO: 实现文件解析 + Chunking + Embedding 入库
    return {
        "success": True,
        "data": {
            "filename": file.filename,
            "message": "文件上传功能待实现",
        },
    }


@router.get("/sources")
async def list_sources():
    """
    知识库文档列表
    """
    # TODO: 从 VectorDB 获取统计
    return {
        "success": True,
        "data": [],
    }
