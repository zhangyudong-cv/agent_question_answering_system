@echo off

REM Neo4j Admin��������
REM ������Neo4j 2025.02.0�����߰汾
REM ����ʱ��: 2026-04-05 23:20:51

neo4j-admin database import full neo4j --overwrite-destination ^
  --nodes=Product="f:\agent_project\deepseek_agent\llm_backend\app\graphrag\origin_data\data\neo4j_admin\product_nodes.csv" ^
  --nodes=Category="f:\agent_project\deepseek_agent\llm_backend\app\graphrag\origin_data\data\neo4j_admin\category_nodes.csv" ^
  --nodes=Supplier="f:\agent_project\deepseek_agent\llm_backend\app\graphrag\origin_data\data\neo4j_admin\supplier_nodes.csv" ^
  --nodes=Customer="f:\agent_project\deepseek_agent\llm_backend\app\graphrag\origin_data\data\neo4j_admin\customer_nodes.csv" ^
  --nodes=Employee="f:\agent_project\deepseek_agent\llm_backend\app\graphrag\origin_data\data\neo4j_admin\employee_nodes.csv" ^
  --nodes=Shipper="f:\agent_project\deepseek_agent\llm_backend\app\graphrag\origin_data\data\neo4j_admin\shipper_nodes.csv" ^
  --nodes=Order="f:\agent_project\deepseek_agent\llm_backend\app\graphrag\origin_data\data\neo4j_admin\order_nodes.csv" ^
  --nodes=Review="f:\agent_project\deepseek_agent\llm_backend\app\graphrag\origin_data\data\neo4j_admin\review_nodes.csv" ^
  --relationships=BELONGS_TO="f:\agent_project\deepseek_agent\llm_backend\app\graphrag\origin_data\data\neo4j_admin\product_category_edges.csv" ^
  --relationships=SUPPLIED_BY="f:\agent_project\deepseek_agent\llm_backend\app\graphrag\origin_data\data\neo4j_admin\product_supplier_edges.csv" ^
  --relationships=PLACED="f:\agent_project\deepseek_agent\llm_backend\app\graphrag\origin_data\data\neo4j_admin\customer_order_edges.csv" ^
  --relationships=PROCESSED="f:\agent_project\deepseek_agent\llm_backend\app\graphrag\origin_data\data\neo4j_admin\employee_order_edges.csv" ^
  --relationships=SHIPPED_VIA="f:\agent_project\deepseek_agent\llm_backend\app\graphrag\origin_data\data\neo4j_admin\order_shipper_edges.csv" ^
  --relationships=CONTAINS="f:\agent_project\deepseek_agent\llm_backend\app\graphrag\origin_data\data\neo4j_admin\order_product_edges.csv" ^
  --relationships=REPORTS_TO="f:\agent_project\deepseek_agent\llm_backend\app\graphrag\origin_data\data\neo4j_admin\employee_reports_to_edges.csv" ^
  --relationships=WROTE="f:\agent_project\deepseek_agent\llm_backend\app\graphrag\origin_data\data\neo4j_admin\customer_review_edges.csv" ^
  --relationships=ABOUT="f:\agent_project\deepseek_agent\llm_backend\app\graphrag\origin_data\data\neo4j_admin\review_product_edges.csv" ^
  --delimiter="," ^
  --array-delimiter=";" ^
  --skip-bad-relationships=true ^
  --skip-duplicate-nodes=true
