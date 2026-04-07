from pydantic import BaseModel, Field
from dataclasses import dataclass, field
from typing import Annotated, Literal, TypedDict, List
from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages


class Router(TypedDict):
    """Classify user query."""
    logic: str
    type: Literal["general-query", "additional-query", "graphrag-query", "image-query", "file-query"]
    question: str = field(default_factory=str)
#路径分发器
class GradeHallucinations(BaseModel):
    """Binary score for hallucination present in generation answer."""

    binary_score: str = Field(
        description="Answer is grounded in the facts, '1' or '0'"
    )

# @dataclass(kw_only=True)： 强制要求数据类中的所有字段必须以关键字参数的形式提供。即不能以位置参数的方式传递。
@dataclass(kw_only=True)
class InputState:
    """Represents the input state for the agent.

    This class defines the structure of the input state, which includes
    the messages exchanged between the user and the agent. 
    """

    messages: Annotated[list[AnyMessage], add_messages]
    
    """Messages track the primary execution state of the agent.

    Typically accumulates a pattern of Human/AI/Human/AI messages; if
    you were to combine this template with a tool-calling ReAct agent pattern,
    it may look like this:

    1. HumanMessage - user input
    2. AIMessage with .tool_calls - agent picking tool(s) to use to collect
         information
    3. ToolMessage(s) - the responses (or errors) from the executed tools
    
        (... repeat steps 2 and 3 as needed ...)
    4. AIMessage without .tool_calls - agent responding in unstructured
        format to the user.

    5. HumanMessage - user responds with the next conversational turn.

        (... repeat steps 2-5 as needed ... )
    

    Merges two lists of messages, updating existing messages by ID.

    By default, this ensures the state is "append-only", unless the
    new message has the same ID as an existing message.
    

    Returns:
        A new list of messages with the messages from `right` merged into `left`.
        If a message in `right` has the same ID as a message in `left`, the
        message from `right` will replace the message from `left`."""
    

# @dataclass(kw_only=True)： 强制要求数据类中的所有字段必须以关键字参数的形式提供。即不能以位置参数的方式传递。
@dataclass(kw_only=True)
class AgentState(InputState):
    """State of the retrieval graph / agent."""
    router: Router = field(default_factory=lambda: Router(type="general-query", logic=""))
    """The router's classification of the user's query."""
    steps: list[str] = field(default_factory=list)
    """Populated by the retriever. This is a list of documents that the agent can reference."""
    question: str = field(default_factory=str) 
    answer: str = field(default_factory=str)  
    hallucination: GradeHallucinations = field(default_factory=lambda: GradeHallucinations(binary_score="0"))
# AgentState 及其相关类的参数详解：
"""
1. Router (TypedDict) - 路由分发器结果：
   - logic (str): AI 判断该意图的理由或逻辑思考过程。
   - type (Literal): 具体的意图分类。
       - "general-query": 闲聊、问候或简单常识。
       - "additional-query": 用户信息不足，需要引导用户补充。
       - "graphrag-query": 需要查询 Neo4j 知识图谱的业务问题。
       - "image-query": 用户上传了图片相关的问题。
       - "file-query": 涉及上传文件分析的问题。
   - question (str): AI 转换后的核心问题或关键词。

2. GradeHallucinations (BaseModel) - 幻觉检测打分：
   - binary_score (str): 只有两个值，"1" 表示回答基于事实（无幻觉），"0" 表示回答存在幻觉或推测。

3. InputState (dataclass) - 外部输入状态：
   - messages (List[AnyMessage]): 用户的原始输入消息列表，以及后续累积的对话历史（HumanMessage, AIMessage）。

4. AgentState (dataclass) - 内部全局状态（继承自 InputState）：
   - messages: 同上（由 InputState 继承而来，由于使用了 add_messages，新消息会自动流转到现有列表中）。
   - router: 当前对话的路由分析结果，指导下一环节往哪走。
   - steps (list[str]): 记录 Agent 的执行步骤，或存储中间检索到的参考文档/段落。
   - question: 当前正在处理的问题原文或简化版。
   - answer: 最终生成的待回复文本内容。
   - hallucination: 幻觉检测的最终得分状态。

5. 字段更新逻辑说明：
   - 【累积附加 (Append)】：
       - messages: 这是图中唯一的自动累积字段。因为它使用了 `Annotated[..., add_messages]`，每次节点返回新消息时，它都会被追加到对话历史中，而不是替换。
   - 【随时更新 (Overwrite)】：
       - router, steps, question, answer, hallucination: 
         这些字段默认采用“覆盖”模式。即如果 A 节点产出了一个 router，B 节点也返回一个 router，那么 B 的结果会直接覆盖 A 的结果。这保证了状态始终反映的是最新的处理结果。
"""
#   注意第一行代码：class AgentState(InputState): 因为它直接继承了 InputState，所以它自然而然地带上了那个能够不断累积的 messages 列表。也就是说，系统既有整个历史对话的“记忆”。

# 2. 这里的其他字段是“覆盖（Overwrite）”而不是累积的！
# 这是它与 messages 最大、最核心的区别！仔细看这里的字段定义：

# python
# router: Router = field(...)
# steps: list[str] = field(...)
# question: str = field(...)
# answer: str = field(...)
# hallucination: GradeHallucinations = field(...)
# 注意，这里没有使用类似 Annotated[..., add_messages] 或者 Annotated[list, operator.add] 这样的归约器（Reducer）。

# 在 LangGraph 的默认机制下，没有 Reducer 的字段在被更新时，新值会**完全覆盖（Overwrite）**旧值。

# 3. 具体过程演示 (为什么必须覆盖？)
# 假设你在和 Agent 进行两次对话：

# 第一轮：用户问“扫地机器人多少钱？”

# 【节点分析】把 router 覆盖为：type="graphrag-query"。
# 【节点检索】查完数据库后，把生成的答案存进去，覆盖 answer 为：“扫地机器人1999元。”。
# 【检验节点】把 hallucination 覆盖为：“1”（没说胡话）。
# 结束，前端输出 1999 元。
# 第二轮：用户紧接着问“你好呀，今天天气真不错”

# 【节点分析】系统开始新一轮的执行。意图识别发现是闲聊，于是把 router 覆盖为：type="general-query"（清除了上一轮的知识库查询标记）。
# 【节点回复】把 answer 覆盖为：“你好！今天天气是不错呢~” （清除了上一轮的 1999元）。
# 【此轮因为是闲聊，可能不需要验幻觉，或者重新覆盖得分为新的值】。
# 为什么要有这种设计（意义所在）？
# 这就是非常经典的 “长期记忆 + 短期工作区” 的架构：

# 长期记忆（messages）：留作历史参考，只增不减（直到触发特定的上下文清理逻辑）。
# 短期工作区（router, answer, hallucination 等）：用完即弃！它们的存在仅仅是为了帮助当前这一句话，在图的各个车间（节点）之间顺利流转、审批、修改。一旦大模型把最终答案通过 API 返回给了用户，这些短期变量在下一轮新对话进来时，就会被统统刷新重写，以防止类似上一轮的“幻觉分数”干扰这一轮的判断。
# 总结一句话： AgentState 就是让 AI 在处理你当前这句提问时用来“打草稿”的地方，打完草稿擦掉，但你们聊过的“所有聊天记录（messages）”会被一直留着。