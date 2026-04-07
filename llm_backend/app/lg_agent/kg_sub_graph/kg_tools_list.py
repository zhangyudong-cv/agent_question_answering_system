from pydantic import BaseModel
from pydantic import Field


class cypher_query(BaseModel):
    """如果用户问的是关于统计数量（例如“处理了多少个订单”、“总数是多少”）、产品价格、库存、规格等，或者需要进行聚合计算的问题，则！必须！使用这个工具，动态生成含有 count() 等聚合函数的Cypher查询语句进行精确查询。
    前提是要在predefined_cypher工具的描述函数中没有一模一样的（尤其注意对于“多少个”的统计问题，预定义工具大多只返回明细列表，因此必须跳到这里生成）才会跳到这里来生成"""

    task: str = Field(..., description="The task the Cypher query must answer.")

class predefined_cypher(BaseModel):
    """这个工具包含预定义的Cypher查询语句，用于快速响应各种电商场景的查询需求（主要是拉取明细列表数据）。
    ！！！【数据完整性规则】：在提取参数（如 $product_name）时，必须！！！100%保留用户输入的原样字符串！！！包括所有的空格、大小写、特殊符号。严禁删除或压缩空格（例如：“华为 智能空调” 不能变成 “华为智能空调”），否则会导致数据库检索失败。
    ！！！【极度重要规则】！！！：假设你要使用这里的工具，那么这个工具返回的字段必须！完全满足！用户的任务需求。
    如果用户问的是“统计数量”（比如：“处理了多少个订单”、“一共几个”），而当前工具列表中的结果只返回“明细列表”（如：返回订单ID、日期等），这就叫“不满足任务需求”！这种情况下，绝对不要用这个工具！！！必须走 cypher_query 工具去让模型动态生成带 count() 的查询！
    
    根据用户问题的类型，可以选择以下类别的查询：
    
      1. 产品类 (Product)：
       - product_by_name: 【参数：$product_name】逻辑：根据产品名称进行模糊匹配。结果：返回产品名、单价、库存及分类名。适用于产品基本信息查询。
       - product_by_category: 【参数：$category_name】逻辑：查询指定分类下的产品。结果：返回产品名、单价、库存。
       - product_by_supplier: 【参数：$supplier_name】逻辑：查询指定供应商供应的产品。结果：返回产品名、单价、库存。
       - products_low_stock: 【参数：$threshold】逻辑：查找库存低于阈值的商品。结果：按库存升序排列。适用于缺货预警。
       - products_popular: 【无需参数】逻辑：基于评论数量统计最受欢迎的前10个产品。结果：返回产名、评论数、平均评分。
    
    2. 客户类 (Customer)：
       - customer_by_name: 【参数：$customer_name】逻辑：查询客户公司信息。结果：返回公司名、联系人、电话及国家。
       - customer_orders: 【参数：$customer_name】逻辑：查询客户的所有历史订单。结果：返回订单ID、下单日期、发货日期。
       - customer_purchase_history: 【参数：$customer_name】逻辑：查询客户买过哪些商品。结果：返回产品名、购买日期、单价。
    
    3. 订单类 (Order)：
       - order_by_id: 【参数：$order_id】逻辑：查询具体订单状态。结果：返回下单日期、要求日期、发货日期及下单公司名。
       - order_details: 【参数：$order_id】逻辑：查询订单明细。结果：列出订单内所有商品、数量、单价及行总计。
       - recent_orders: 【无需参数】逻辑：检索最新的10笔订单。结果：返回订单ID、日期和下单公司名。
       - delayed_orders: 【无需参数】逻辑：检索未按时发货或超时未发的订单。结果：返回详情及受影响的下单公司。
    
    4. 员工类 (Employee)：
       - employee_by_name: 【参数：$employee_name】逻辑：查询员工档案。结果：返回姓名、职位、入职日期。
       - employee_processed_orders: 【参数：$employee_name】逻辑：查询员工经手的具体订单。结果：按时间倒序列出订单及对应的下单客户公司名。
    
    5. 分析与评价类：
       - product_reviews: 【参数：$product_name】逻辑：查看产品的用户反馈。结果：返回买家名、评分、评价正文、日期。
       - top_rated_products: 【无需参数】逻辑：查找评分最高的优质商品（评论需>3条）。结果：返回前10名及评分详情。
       - product_sales: 【参数：$product_name】逻辑：统计单品的历史销售总金额。
       - category_sales: 【无需参数】逻辑：按分类统计销售业绩。结果：返回各分类销售总额排名。
       - monthly_sales: 【无需参数】逻辑：分析各个月份的销售趋势。结果：按月统计总销售额。
    
    6. 智能家居专项 (Smart Home)：
       - smart_home_products: 检索所有包含“智能”字样的产品。
       - smart_speakers / smart_lighting: 快速检索智能音箱或智能照明类专项产品。
    
    提示：如果用户问题不仅限于以上固定场景（例如涉及多表关联、复杂数值过滤，尤其是要求【统计具体数量或求和】如“多少个订单”、“总销售额是多少”），请坚决改用 cypher_query 工具生成动态 Cypher进行精确查询！
    请根据用户的问题选择最合适的查询，并根据需要替换查询中的参数值（如$product_name, $category_name等）。
    【最后警告】：问的问题要和上面的“结果”完美对上才使用这个工具！（如果是问“多少个”，但上面结果是“列出订单明细”，则坚决不能用！），否则必须使用 cypher_query 工具或者 microsoft_graphrag_query 工具。
    """

    query: str = Field(..., description="query the graph must include the question")
    parameters: dict = Field(..., description="parameters for the query to Neo4j. IMPORTANT: MUST preserve original spaces and casing for values like 'product_name'.")

class microsoft_graphrag_query(BaseModel):
    """如果用户问的问题是关于产品的故障、售后、保修、维修、退换货以及评价等，则使用这个工具"""
    query: str = Field(..., description="query the graph must include the question")
    

class real_time_network_query(BaseModel):
    """如果用户问的问题是关于一些实时的产品有效信息需要联网检索的话，则使用这个工具"""
    query: str = Field(..., description="query the network must include the question")


