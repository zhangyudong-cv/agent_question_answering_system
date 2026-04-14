from fastapi import FastAPI, HTTPException, UploadFile, File, Query, Form, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
import redis.asyncio as aioredis
import aio_pika
from app.services.llm_factory import LLMFactory
from app.services.search_service import SearchService
from fastapi.staticfiles import StaticFiles
from datetime import datetime
from pathlib import Path
import asyncio
from sqlalchemy import text
from app.lg_agent.kg_sub_graph.kg_neo4j_conn import get_neo4j_graph

from app.core.logger import get_logger, log_structured
from app.core.middleware import LoggingMiddleware
from app.core.config import settings
from app.api import api_router
from app.core.database import AsyncSessionLocal
from app.models.conversation import Conversation, DialogueType
from app.models.message import Message
from app.core.security import get_current_user
from app.models.user import User
from sqlalchemy import select
from app.services.conversation_service import ConversationService
import uuid
import os
from app.services.indexing_service import IndexingService
import sys
from app.lg_agent.lg_states import AgentState, InputState
from app.lg_agent.utils import new_uuid
from app.lg_agent.lg_builder import builder, graph
from langgraph.checkpoint.redis import AsyncRedisSaver
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command
import json
from fastapi import Request

import mimetypes

# 强制修复 Windows 下 JS 和 CSS 的 MIME 类型问题
mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("text/css", ".css")

# 配置上传目录 - RAG 功能的
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

from contextlib import asynccontextmanager

# logger 变量初始化
logger = get_logger(service="main")

# 定义消费者逻辑
async def rabbitmq_consumer():
    """
    RabbitMQ 消费者：监听购买消息并同步更新 MySQL 和 Neo4j 库存
    """
    # 从 settings 中读取 RabbitMQ 配置
    rmq_user = settings.RABBITMQ_USER
    rmq_pass = settings.RABBITMQ_PASS
    rmq_host = settings.RABBITMQ_HOST
    rmq_port = settings.RABBITMQ_PORT
    rmq_vhost = settings.RABBITMQ_VHOST
    amqp_url = f"amqp://{rmq_user}:{rmq_pass}@{rmq_host}:{rmq_port}/{rmq_vhost}"
    
    logger.info("RabbitMQ 消费者启动中...")
    
    while True:
        try:
            connection = await aio_pika.connect(amqp_url)
            async with connection:
                channel = await connection.channel()
                # 声明队列（确保队列存在）
                queue = await channel.declare_queue("agentque", durable=True)
                
                logger.info("RabbitMQ 消费者已就绪，正在监听 agentque...")
                
                async with queue.iterator() as queue_iter:
                    async for message in queue_iter:
                        async with message.process():
                            try:
                                data = json.loads(message.body.decode())
                                product_id = data.get("product_id")
                                if not product_id:
                                    continue
                                    
                                logger.info(f"消费者收到订单消息: 产品ID={product_id}")
                                
                                # 1. 更新 MySQL 库存
                                # 深度分析表结构可知：表名 Products, 字段 UnitsInStock, 主键 ProductID
                                async with AsyncSessionLocal() as session:
                                    mysql_sql = text("UPDATE graphrag.Products SET UnitsInStock = UnitsInStock - 1 WHERE ProductID = :id AND UnitsInStock > 0")
                                    result = await session.execute(mysql_sql, {"id": product_id})
                                    await session.commit()
                                    logger.info(f"MySQL 库存更新完成 (ProductID: {product_id})")

                                # 2. 更新 Neo4j 库存
                                try:
                                    neo_graph = get_neo4j_graph()
                                    # Cypher: 匹配 Product 节点并减库存
                                    # 同时兼容字符串和整数类型的 ProductID，确保匹配成功
                                    cypher = "MATCH (p:Product) WHERE p.ProductID = $id OR p.ProductID = toInteger($id) SET p.UnitsInStock = toInteger(p.UnitsInStock) - 1"
                                    # Neo4jGraph.query 是同步方法，使用 to_thread 避免阻塞事件循环
                                    await asyncio.to_thread(neo_graph.query, cypher, {"id": product_id})
                                    logger.info(f"Neo4j 库存更新完成 (ProductID: {product_id})")
                                except Exception as ne:
                                    logger.error(f"Neo4j 库存更新失败: {str(ne)}")

                            except Exception as process_err:
                                logger.error(f"处理消息内容出错: {str(process_err)}")
                                
        except Exception as e:
            logger.error(f"RabbitMQ 消费者连接异常: {str(e)}。5秒后尝试重连...")
            await asyncio.sleep(5)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. 启动时创建一个异步任务运行消费者
    consumer_task = asyncio.create_task(rabbitmq_consumer())
    logger.info("已在独立协程中启动 RabbitMQ 消费者服务")

    # 2. 初始化 LangGraph 的 Redis 持久化层
    # 设计理念：在应用生命周期内保持 Redis 连接，并将其注入到 LangGraph 中
    try:
        from app.lg_agent.lg_builder import get_redis_checkpointer
        cp_gen = get_redis_checkpointer()
        # 进入上下文管理器获取 Redis Saver
        saver = await cp_gen.__aenter__()
        # 编译带持久化功能的图，并存储在 app.state 中
        app.state.graph = builder.compile(checkpointer=saver)
        app.state.saver_gen = cp_gen # 存储生成器以便正式关闭时 __aexit__
        logger.info("LangGraph Redis 持久化层初始化成功")
    except Exception as e:
        logger.error(f"LangGraph Redis 持久化层初始化失败: {e}，将回退到内存模式。")
        app.state.graph = builder.compile(checkpointer=MemorySaver())
        app.state.saver_gen = None

    yield
    # 关闭时取消异步任务与连接
    consumer_task.cancel()
    # 彻底关闭 Redis Saver 连接池
    if hasattr(app.state, "saver_gen") and app.state.saver_gen:
        await app.state.saver_gen.__aexit__(None, None, None)
        
    try:
        await consumer_task
    except asyncio.CancelledError:
        logger.info("RabbitMQ 消费者服务已安全关闭")

# 创建 FastAPI 应用实例，集成生命周期管理
app = FastAPI(title="AssistGen REST API", lifespan=lifespan)

# 添加日志中间件， 使用 LoggingMiddleware 来统一处理日志记录，从而替代 FastAPI 的原生打印日志。
app.add_middleware(LoggingMiddleware)

# CORS设置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中要设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. 用户注册、登录路由通过 api_router 路由挂载到 /api 前缀
app.include_router(api_router, prefix="/api")

class ReasonRequest(BaseModel):
    messages: List[Dict[str, str]]
    user_id: int

class ChatMessage(BaseModel):
    messages: List[Dict[str, str]]
    user_id: int
    conversation_id: int  # 添加会话ID字段

class RAGChatRequest(BaseModel):
    messages: List[Dict[str, str]]
    index_id: str
    user_id: int

class CreateConversationRequest(BaseModel):
    user_id: int

class UpdateConversationNameRequest(BaseModel):
    name: str

class LangGraphRequest(BaseModel):
    query: str
    user_id: int
    conversation_id: Optional[str] = None
    image: Optional[UploadFile] = None

class LangGraphResumeRequest(BaseModel):
    query: str
    user_id: int
    conversation_id: str

class ProductPurchaseRequest(BaseModel):
    product_id: str


@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/api/chat")
async def chat_endpoint(request: ChatMessage):
    """聊天接口"""
    try:
        logger.info(f"Processing chat request for user {request.user_id} in conversation {request.conversation_id}")
        chat_service = LLMFactory.create_chat_service()
        
        return StreamingResponse(
            chat_service.generate_stream(
                messages=request.messages,
                user_id=request.user_id,
                conversation_id=request.conversation_id,
                on_complete=ConversationService.save_message
            ),
            media_type="text/event-stream"
        )
    except Exception as e:
        logger.error(f"Chat error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/reason")
async def reason_endpoint(request: ReasonRequest):
    """推理接口"""
    try:
        logger.info(f"Processing reasoning request for user {request.user_id}")
        reasoner = LLMFactory.create_reasoner_service()
        
        log_structured("reason_request", {
            "user_id": request.user_id,
            "message_count": len(request.messages),
            "last_message": request.messages[-1]["content"][:100] + "..."
        })
        
        return StreamingResponse(
            reasoner.generate_stream(request.messages),
            media_type="text/event-stream"
        )
    
    except Exception as e:
        logger.error(f"Reasoning error for user {request.user_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/search")
async def search_endpoint(request: ChatMessage):
    """带搜索功能的聊天接口"""
    try:
        logger.info(f"Processing search request for user {request.user_id} in conversation {request.conversation_id}")
        logger.info(f"Request: {request}")
        search_service = LLMFactory.create_search_service()
        return StreamingResponse(
            search_service.generate_stream(
                query=request.messages[0]["content"],
                user_id=request.user_id,
                conversation_id=request.conversation_id,
                # on_complete=ConversationService.save_message
            ),
            media_type="text/event-stream"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload")
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user_id: int = Form(...)
):
    """上传文件并准备 RAG 处理"""
    try:
        logger.info(f"Uploading file for user {user_id}: {file.filename}")
        
        # 1. 创建基于UUID的一级目录
        user_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"user_{user_id}"))
        first_level_dir = UPLOAD_DIR / user_uuid
        
        # 2. 创建基于时间戳的二级目录
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        second_level_dir = first_level_dir / timestamp
        second_level_dir.mkdir(parents=True, exist_ok=True)
        
        # 3. 生成带时间戳的文件名
        original_name, ext = os.path.splitext(file.filename)
        new_filename = f"{original_name}_{timestamp}{ext}"
        file_path = second_level_dir / new_filename
        
        # 保存文件
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
            
        # 获取文件信息
        file_info = {
            "filename": new_filename,
            "original_name": file.filename,
            "size": len(content),
            "type": file.content_type,
            "path": str(file_path).replace('\\', '/'),
            "user_id": user_id,
            "user_uuid": user_uuid,
            "upload_time": timestamp,
            "directory": str(second_level_dir)
        }
        
        # 4. 处理文件索引（作为后台任务运行，避免前端长时间等待超时）
        indexing_service = IndexingService()
        background_tasks.add_task(indexing_service.process_file, file_info)
        
        # 合并结果并提前返回 (构造伪装的 index_result 以免前端旧代码因找不到该字段而 JS 报错报错卡死)
        result = {
            **file_info, 
            "status": "indexing_started", 
            "message": "文件已上传成功，知识库索引正在后台加紧构建中！",
            "index_result": {
                "status": "success",  # 关键点：欺骗前端让它认为成功了从而关闭上传中的圈圈
                "message": "后台构建中",
                "is_update": False,
                "input_dir": "",
                "output_dir": ""
            }
        }
        
        return result
        
    except Exception as e:
        logger.exception(f"Upload failed for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat-rag")
async def rag_chat_endpoint(request: RAGChatRequest):
    """基于文档的问答接口"""
    try:
        logger.info(f"Processing RAG chat request for user {request.user_id}")
        rag_chat_service = RAGChatService()
        
        return StreamingResponse(
            rag_chat_service.generate_stream(
                request.messages,
                request.index_id
            ),
            media_type="text/event-stream"
        )
    except Exception as e:
        logger.error(f"RAG chat error for user {request.user_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/conversations")
async def create_conversation(request: CreateConversationRequest):
    """创建新会话"""
    try:
        conversation_id = await ConversationService.create_conversation(request.user_id)
        return {"conversation_id": conversation_id}
    except Exception as e:
        logger.error(f"Error creating conversation: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
#左侧历史会话
@app.get("/api/conversations/user/{user_id}")
async def get_user_conversations(user_id: int):
    """获取用户的所有会话"""
    try:
        conversations = await ConversationService.get_user_conversations(user_id)
        return conversations
    except Exception as e:
        logger.error(f"Error getting conversations: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
#单个历史会话
@app.get("/api/conversations/{conversation_id}/messages")
async def get_conversation_messages(conversation_id: int, user_id: int):
    """获取会话的所有消息"""
    try:
        messages = await ConversationService.get_conversation_messages(conversation_id, user_id)
        return messages
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting messages: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/conversations/{conversation_id}")
async def delete_conversation(conversation_id: int):
    """删除会话及其所有消息"""
    try:
        conversation_service = ConversationService()
        await conversation_service.delete_conversation(conversation_id)
        return {"message": "会话已删除"}
    except Exception as e:
        logger.error(f"删除会话失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/conversations/{conversation_id}/name")
async def update_conversation_name(
    conversation_id: int,
    request: UpdateConversationNameRequest
):
    """修改会话名称"""
    try:
        conversation_service = ConversationService()
        await conversation_service.update_conversation_name(conversation_id, request.name)
        return {"message": "会话名称已更新"}
    except Exception as e:
        logger.error(f"更新会话名称失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/langgraph/query")
async def langgraph_query(
    request: Request,
    query: str = Form(...),
    user_id: int = Form(...),
    conversation_id: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None)
):
    """使用LangGraph处理用户查询，支持图片上传"""
    try:
        logger.info(f"Processing LangGraph query for user {user_id} and conversation {conversation_id}")
        
        # 处理图片上传
        image_path = None
        if image:
            # 创建图片存储目录
            image_dir = Path("uploads/images")
            image_dir.mkdir(parents=True, exist_ok=True)
            
            # 生成带时间戳的文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            original_name, ext = os.path.splitext(image.filename)
            new_filename = f"{original_name}_{timestamp}{ext}"
            image_path = image_dir / new_filename
            
            # 保存图片
            content = await image.read()
            with open(image_path, "wb") as f:
                f.write(content)
            
            logger.info(f"Saved image {new_filename} for user {user_id}")
        
        # 获取当前图谱实例
        graph = request.app.state.graph
        
        # 优化：使用 user_id 构造 thread_id，实现跨进程/会话的用户历史记忆共享
        # 存入 Redis 的 Key 将包含此 ID，确保多场景下能记住最近的五段（10条）对话
        thread_id = f"user_{user_id}"
        thread_config = {
            "configurable": {
                "thread_id": thread_id, 
                "user_id": user_id,
                "conversation_id": conversation_id, # 保留原始会话 ID 供参考
                "image_path": str(image_path) if image_path else None
            }
        }
        
        # 获取当前线程状态
        state_history = None
        try:
            # 检查是否有现有的会话状态
            if thread_id:
                state_history = await graph.aget_state(thread_config)
                if state_history:
                    logger.info(f"Found existing conversation state for thread_id: {thread_id}")
        except Exception as e:
            logger.warning(f"Error retrieving state: {e}. Starting with fresh state.")
        
        # 准备输入状态 - 如果是现有会话，直接传入查询文本
        if state_history and len(state_history) > 0 and len(state_history[-1]) > 0:
            logger.info("Using existing conversation state")
            # 如果有现有会话，使用resume命令继续对话
            async def process_stream():
                async for c, metadata in graph.astream(
                    Command(resume=query), 
                    stream_mode="messages", 
                    config=thread_config
                ):
                    # 只处理最终展示给用户的内容，跳过中间工具调用和内部状态
                    if c.content and "research_plan" not in metadata.get("tags", []) and not c.additional_kwargs.get("tool_calls"):
                        # 关键修改：使用json.dumps处理content，确保特殊字符如换行符被正确处理
                        content_json = json.dumps(c.content, ensure_ascii=False)
                        yield f"data: {content_json}\n\n"
                        
                    # 工具调用单独处理，不发送给前端
                    elif c.additional_kwargs.get("tool_calls"):
                        tool_data = c.additional_kwargs.get("tool_calls")[0]["function"].get("arguments")
                        logger.debug(f"Tool call: {tool_data}")
                        
                # 处理中断情况
                state = await graph.aget_state(thread_config)
                if len(state) > 0 and len(state[-1]) > 0:
                    if len(state[-1][0].interrupts) > 0:
                        interrupt_json = json.dumps({"interruption": True, "conversation_id": thread_id})
                        yield f"data: {interrupt_json}\n\n"
        else:
            # 新会话或找不到现有状态，创建新的输入状态
            logger.info("Creating new conversation state")
            input_state = InputState(messages=query)
            
            # 流式处理查询
            async def process_stream():
                async for c, metadata in graph.astream(
                    input=input_state, 
                    stream_mode="messages", 
                    config=thread_config
                ):
                    # 只处理最终展示给用户的内容，跳过中间工具调用和内部状态
                    if c.content and "research_plan" not in metadata.get("tags", []) and not c.additional_kwargs.get("tool_calls"):
                        # 关键修改：使用json.dumps处理content，确保特殊字符如换行符被正确处理
                        content_json = json.dumps(c.content, ensure_ascii=False)
                        yield f"data: {content_json}\n\n"
                        
                    # 工具调用单独处理，不发送给前端
                    elif c.additional_kwargs.get("tool_calls"):
                        tool_data = c.additional_kwargs.get("tool_calls")[0]["function"].get("arguments")
                        logger.debug(f"Tool call: {tool_data}")
                        
                # 处理中断情况
                state = await graph.aget_state(thread_config)
                if len(state) > 0 and len(state[-1]) > 0:
                    if len(state[-1][0].interrupts) > 0:
                        interrupt_json = json.dumps({"interruption": True, "conversation_id": thread_id})
                        yield f"data: {interrupt_json}\n\n"
        
        response = StreamingResponse(
            process_stream(),
            media_type="text/event-stream"
        )
        
        # 添加会话ID到响应头，方便前端获取
        response.headers["X-Conversation-ID"] = thread_id
        
        return response
        
    except Exception as e:
        logger.error(f"LangGraph query error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/langgraph/resume")
async def langgraph_resume(request_body: LangGraphResumeRequest, request: Request):
    """继续执行LangGraph流程"""
    graph = request.app.state.graph
    try:
        logger.info(f"Resuming LangGraph query for user {request_body.user_id} with conversation {request_body.conversation_id}")
        
        # 优化：统一使用 user_id 标识符作为线程 ID，确保记忆在恢复流程中也能一致
        thread_id = f"user_{request_body.user_id}"
        thread_config = {
            "configurable": {
                "thread_id": thread_id,
                "user_id": request_body.user_id,
                "conversation_id": request_body.conversation_id
            }
        }
        
        # 流式处理恢复
        async def process_resume():
            async for c, metadata in graph.astream(Command(resume=request_body.query), stream_mode="messages", config=thread_config):
                # 只处理最终展示给用户的内容
                if c.content and not c.additional_kwargs.get("tool_calls"):
                    # 同样使用json.dumps处理内容
                    content_json = json.dumps(c.content, ensure_ascii=False)
                    yield f"data: {content_json}\n\n"
                
                # 工具调用单独处理，不发送给前端
                elif c.additional_kwargs.get("tool_calls"):
                    tool_data = c.additional_kwargs.get("tool_calls")[0]["function"].get("arguments")
                    logger.debug(f"Tool call: {tool_data}")
        
        return StreamingResponse(
            process_resume(),
            media_type="text/event-stream"
        )
        
    except Exception as e:
        logger.error(f"LangGraph resume error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload/image")
async def upload_image(
    image: UploadFile = File(...),
    user_id: int = Form(...),
    conversation_id: Optional[str] = Form(None)
):
    """上传图片并返回图片存储路径"""
    try:
        # 创建图片存储目录
        image_dir = Path("uploads/images")
        if conversation_id:
            image_dir = image_dir / conversation_id
        image_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成带时间戳的文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        original_name, ext = os.path.splitext(image.filename)
        new_filename = f"{original_name}_{timestamp}{ext}"
        image_path = image_dir / new_filename
        
        # 保存图片
        content = await image.read()
        with open(image_path, "wb") as f:
            f.write(content)
        
        # 获取图片信息
        image_info = {
            "filename": new_filename,
            "original_name": image.filename,
            "size": len(content),
            "type": image.content_type,
            "path": str(image_path).replace('\\', '/'),
            "user_id": user_id,
            "conversation_id": conversation_id,
            "upload_time": timestamp
        }
        
        logger.info(f"Image uploaded: {image_info}")
        
        return image_info
        
    except Exception as e:
        logger.error(f"Image upload failed for user {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/product/purchase")
async def purchase_product(
    request: ProductPurchaseRequest, 
    current_user: User = Depends(get_current_user)
):
    """
    商品购买接口：Redis 控制超卖 + RabbitMQ 异步解耦
    根据用户请求的产品ID、校验库存并扣减，最后通过MQ通知下游系统。
    """
    product_id = request.product_id
    user_id = current_user.id
    
    # 1. 业务逻辑：Redis 原子扣减库存防止超卖
    # 使用 aioredis 异步连接
    redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    redis_key = f"product:{product_id}"

    try:
        # DECR 是原子递减操作，返回递减之后的值
        new_inventory = await redis_client.decr(redis_key)
        
        if new_inventory < 0:
            # 库存不足，立即回退原子操作
            await redis_client.incr(redis_key)
            logger.warning(f"用户 {user_id} 购买产品 {product_id} 失败：库存不足")
            raise HTTPException(status_code=400, detail="商品库存不足，手慢无！")
            
        logger.info(f"用户 {user_id} 购买产品 {product_id} 成功，当前库存：{new_inventory}")

        # 2. 消息发送：RabbitMQ 参数按照要求配置
        # 建立 RabbitMQ 连接
        # 从 settings 中读取 RabbitMQ 配置
        rmq_user = settings.RABBITMQ_USER
        rmq_pass = settings.RABBITMQ_PASS
        rmq_host = settings.RABBITMQ_HOST
        rmq_port = settings.RABBITMQ_PORT
        rmq_vhost = settings.RABBITMQ_VHOST
        
        # 构造 AMQP URL
        amqp_url = f"amqp://{rmq_user}:{rmq_pass}@{rmq_host}:{rmq_port}/{rmq_vhost}"
        
        try:
            connection = await aio_pika.connect(amqp_url)
            async with connection:
                channel = await connection.channel()
                
                # 定义交换机名字为 agentchange
                exchange = await channel.declare_exchange(
                    "agentchange", 
                    aio_pika.ExchangeType.DIRECT, 
                    durable=True
                )
                
                # 定义队列名字为 agentque
                queue = await channel.declare_queue("agentque", durable=True)
                
                # 把队列和交换机绑定到一起
                await queue.bind(exchange, routing_key="product_purchase_routing")
                
                # 发送 product_id 到消息队列
                message_body = json.dumps({
                    "product_id": product_id,
                    "user_id": user_id,
                    "timestamp": datetime.now().isoformat()
                })
                
                await exchange.publish(
                    aio_pika.Message(body=message_body.encode()),
                    routing_key="product_purchase_routing"
                )
                
                logger.info(f"已将产品 {product_id} 的购买消息发送到 RabbitMQ (agentque)")

        except Exception as mq_err:
            # 注意：实际生产中如果MQ发送失败，需要有补偿机制或者写库操作。这里记录日志
            logger.error(f"发送消息到 MQ 失败: {str(mq_err)}")
            # 这里不抛出异常，因为库存已经扣减成功，可以后期同步或通知管理员
            
        return {
            "status": "success",
            "message": "下单成功",
            "product_id": product_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"处理购买请求出错: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="服务器繁忙，请稍后再试")
    finally:
        await redis_client.close()


@app.post("/api/product/purchase/direct")
async def purchase_product_direct(
    request: ProductPurchaseRequest, 
    current_user: User = Depends(get_current_user)
):
    """
    同步下单接口（直接操作数据库）：对标异步解耦方案。
    逻辑：1. MySQL 事务内扣减库存 2. Neo4j 同步更新
    字段：Products, UnitsInStock, ProductID (严格按照 consumer 要求)
    """
    product_id = request.product_id
    user_id = current_user.id
    
    logger.info(f"用户 {user_id} 发起同步下单请求 (ProductID: {product_id})")

    try:
        # 1. 操作 MySQL (使用原子更新)
        async with AsyncSessionLocal() as session:
            # 采用原子扣减逻辑：UPDATE ... SET ... WHERE ... AND UnitsInStock > 0
            # 严格遵循 Products 表和 ProductID 字段
            mysql_sql = text("""
                UPDATE graphrag.Products 
                SET UnitsInStock = UnitsInStock - 1 
                WHERE ProductID = :id AND UnitsInStock > 0
            """)
            
            result = await session.execute(mysql_sql, {"id": product_id})
            await session.commit()
            
            # 检查是否有行受影响（如果库存为 0，rowcount 会为 0）
            if result.rowcount == 0:
                logger.warning(f"MySQL 同步扣减失败：ID {product_id} 库存不足或商品不存在")
                raise HTTPException(status_code=400, detail="商品库存不足，下单失败！")

        # 2. 操作 Neo4j (同步扣减)
        # 严格遵循 MATCH (p:Product) 和 p.ProductID 等字符
        try:
            neo_graph = get_neo4j_graph()
            cypher = """
                MATCH (p:Product) 
                WHERE p.ProductID = $id OR p.ProductID = toInteger($id) 
                SET p.UnitsInStock = toInteger(p.UnitsInStock) - 1
            """
            # 使用 to_thread 避免同步网络 IO 阻塞 FastAPI
            await asyncio.to_thread(neo_graph.query, cypher, {"id": product_id})
            logger.info(f"Neo4j 同步库存更新完成 (ProductID: {product_id})")
        except Exception as ne:
            # 即使 Neo4j 失败，也记录日志并警告
            logger.error(f"Neo4j 同步更新出现次级故障: {str(ne)}")
            
        return {
            "status": "success",
            "message": "同步下单成功（直接写入库）",
            "product_id": product_id,
            "user_id": user_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"同步下单系统崩溃: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="服务器处理直连扣减时出错")


# 最后挂载静态文件，并确保使用绝对路径
STATIC_DIR = Path(__file__).parent / "static" / "dist"
app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
