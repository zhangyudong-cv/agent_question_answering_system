@echo off

REM Neo4j Admin导入命令
REM 适用于Neo4j 2025.02.0及更高版本
REM 生成时间: 2026-04-05 22:07:22

neo4j-admin database import full neo4j --overwrite-destination ^
  --nodes=Product="F:\agent_project\deepseek_agent\data\neo4j_admin\product_nodes.csv" ^
  --nodes=Category="F:\agent_project\deepseek_agent\data\neo4j_admin\category_nodes.csv" ^
  --nodes=Supplier="F:\agent_project\deepseek_agent\data\neo4j_admin\supplier_nodes.csv" ^
  --nodes=Customer="F:\agent_project\deepseek_agent\data\neo4j_admin\customer_nodes.csv" ^
  --nodes=Employee="F:\agent_project\deepseek_agent\data\neo4j_admin\employee_nodes.csv" ^
  --nodes=Shipper="F:\agent_project\deepseek_agent\data\neo4j_admin\shipper_nodes.csv" ^
  --nodes=Order="F:\agent_project\deepseek_agent\data\neo4j_admin\order_nodes.csv" ^
  --nodes=Review="F:\agent_project\deepseek_agent\data\neo4j_admin\review_nodes.csv" ^
  --relationships=BELONGS_TO="F:\agent_project\deepseek_agent\data\neo4j_admin\product_category_edges.csv" ^
  --relationships=SUPPLIED_BY="F:\agent_project\deepseek_agent\data\neo4j_admin\product_supplier_edges.csv" ^
  --relationships=PLACED="F:\agent_project\deepseek_agent\data\neo4j_admin\customer_order_edges.csv" ^
  --relationships=PROCESSED="F:\agent_project\deepseek_agent\data\neo4j_admin\employee_order_edges.csv" ^
  --relationships=SHIPPED_VIA="F:\agent_project\deepseek_agent\data\neo4j_admin\order_shipper_edges.csv" ^
  --relationships=CONTAINS="F:\agent_project\deepseek_agent\data\neo4j_admin\order_product_edges.csv" ^
  --relationships=REPORTS_TO="F:\agent_project\deepseek_agent\data\neo4j_admin\employee_reports_to_edges.csv" ^
  --relationships=WROTE="F:\agent_project\deepseek_agent\data\neo4j_admin\customer_review_edges.csv" ^
  --relationships=ABOUT="F:\agent_project\deepseek_agent\data\neo4j_admin\review_product_edges.csv" ^
  --delimiter="," ^
  --array-delimiter=";" ^
  --skip-bad-relationships=true ^
  --skip-duplicate-nodes=true
