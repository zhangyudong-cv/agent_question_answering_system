import pandas as pd
import os
import re
from datetime import datetime

def prepare_neo4j_admin_import(data_dir='exported_data', output_dir='data/neo4j_admin'):
    """
    准备Neo4j Admin导入文件，添加适当的标题行
    
    参数:
    data_dir: 输入CSV文件所在目录
    output_dir: 输出Neo4j Admin导入文件目录
    """
    print(f"开始准备Neo4j Admin导入文件...")
    
    # 确保输出目录存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 处理节点文件
    prepare_product_nodes(data_dir, output_dir)
    prepare_category_nodes(data_dir, output_dir)
    prepare_supplier_nodes(data_dir, output_dir)
    prepare_customer_nodes(data_dir, output_dir)
    prepare_employee_nodes(data_dir, output_dir)
    prepare_shipper_nodes(data_dir, output_dir)
    prepare_order_nodes(data_dir, output_dir)
    prepare_review_nodes(data_dir, output_dir)
    
    # 处理边文件
    prepare_product_category_edges(data_dir, output_dir)
    prepare_product_supplier_edges(data_dir, output_dir)
    prepare_customer_order_edges(data_dir, output_dir)
    prepare_employee_order_edges(data_dir, output_dir)
    prepare_order_shipper_edges(data_dir, output_dir)
    prepare_order_product_edges(data_dir, output_dir)
    prepare_employee_reports_to_edges(data_dir, output_dir)
    prepare_review_edges(data_dir, output_dir)
    
    print(f"Neo4j Admin导入文件准备完成，文件保存在: {output_dir}")
    
    # 生成导入命令
    generate_import_command(output_dir)

def prepare_product_nodes(data_dir, output_dir):
    """准备产品节点文件"""
    file_path = os.path.join(data_dir, 'products.csv')
    if not os.path.exists(file_path):
        print(f"警告: 找不到产品数据文件 {file_path}")
        return
    
    try:
        df = pd.read_csv(file_path)
        
        # 先存储原始 ID 列的唃唃唃唃唃唃唃唃唃唃唃唃唃唃唃唃唃唃唃唃唃唃唃唃唃唃-----
        # 关键：不能用自赋値 df['X']=df['X'] 来备份，Pandas 在 rename 后会丢失该列。
        # 正确做法：先把唃唃唃唃唃唃唃唃唃唃唃唃唃唃唃唃唃唃唃唃唃唃唃唃唃唃唃唃唃唃唃唃唃唃唃唃唃唃唃唃唃唃唃唃唃唃唃唃唃唃唃唃唃唃唃唃唃唃唃唃唃唃唃唃唃唃唃唃唃唃唃唃
        product_id_values = df['ProductID'].values
        
        # 重命名ID列为 Neo4j Admin 导入格式的主键标识
        df = df.rename(columns={'ProductID': 'productId:ID(Product)'})
        
        # rename 完成后再写回同名普通属性列，使 Cypher WHERE p.ProductID = x 可正常执行
        df['ProductID'] = product_id_values
        
        # 添加标签列
        df['labels:LABEL'] = 'Product'
        
        # 保存为Neo4j Admin导入格式
        output_file = os.path.join(output_dir, 'product_nodes.csv')
        df.to_csv(output_file, index=False)
        print(f"产品节点文件已保存: {output_file}")
    except Exception as e:
        print(f"处理产品节点时出错: {e}")

def prepare_category_nodes(data_dir, output_dir):
    """准备类别节点文件"""
    file_path = os.path.join(data_dir, 'categories.csv')
    if not os.path.exists(file_path):
        print(f"警告: 找不到类别数据文件 {file_path}")
        return
    
    try:
        df = pd.read_csv(file_path)
        
        # 先把原始 CategoryID 列值存入临时变量
        category_id_values = df['CategoryID'].values
        
        # 重命名ID列为 Neo4j Admin 导入格式的主键标识
        df = df.rename(columns={'CategoryID': 'categoryId:ID(Category)'})
        
        # rename 完成后再写回同名普通属性列，使 Cypher WHERE c.CategoryID = x 可正常执行
        df['CategoryID'] = category_id_values
        
        # 添加标签列
        df['labels:LABEL'] = 'Category'
        
        # 保存为Neo4j Admin导入格式
        output_file = os.path.join(output_dir, 'category_nodes.csv')
        df.to_csv(output_file, index=False)
        print(f"类别节点文件已保存: {output_file}")
    except Exception as e:
        print(f"处理类别节点时出错: {e}")

def prepare_supplier_nodes(data_dir, output_dir):
    """准备供应商节点文件"""
    file_path = os.path.join(data_dir, 'suppliers.csv')
    if not os.path.exists(file_path):
        print(f"警告: 找不到供应商数据文件 {file_path}")
        return
    
    try:
        df = pd.read_csv(file_path)
        
        # 先把原始 SupplierID 列值存入临时变量
        supplier_id_values = df['SupplierID'].values
        
        # 重命名ID列为 Neo4j Admin 导入格式的主键标识
        df = df.rename(columns={'SupplierID': 'supplierId:ID(Supplier)'})
        
        # rename 完成后再写回同名普通属性列，使 Cypher WHERE s.SupplierID = x 可正常执行
        df['SupplierID'] = supplier_id_values
        
        # 添加标签列
        df['labels:LABEL'] = 'Supplier'
        
        # 保存为Neo4j Admin导入格式
        output_file = os.path.join(output_dir, 'supplier_nodes.csv')
        df.to_csv(output_file, index=False)
        print(f"供应商节点文件已保存: {output_file}")
    except Exception as e:
        print(f"处理供应商节点时出错: {e}")

def prepare_customer_nodes(data_dir, output_dir):
    """准备客户节点文件"""
    file_path = os.path.join(data_dir, 'customers.csv')
    if not os.path.exists(file_path):
        print(f"警告: 找不到客户数据文件 {file_path}")
        return
    
    try:
        df = pd.read_csv(file_path)
        
        # 先把原始 CustomerID 列值存入临时变量
        customer_id_values = df['CustomerID'].values
        
        # 重命名ID列为 Neo4j Admin 导入格式的主键标识
        df = df.rename(columns={'CustomerID': 'customerId:ID(Customer)'})
        
        # rename 完成后再写回同名普通属性列，使 Cypher WHERE c.CustomerID = 'AB123' 可正常执行
        df['CustomerID'] = customer_id_values
        
        # 添加标签列
        df['labels:LABEL'] = 'Customer'
        
        # 保存为Neo4j Admin导入格式
        output_file = os.path.join(output_dir, 'customer_nodes.csv')
        df.to_csv(output_file, index=False)
        print(f"客户节点文件已保存: {output_file}")
    except Exception as e:
        print(f"处理客户节点时出错: {e}")

def prepare_employee_nodes(data_dir, output_dir):
    """准备员工节点文件"""
    file_path = os.path.join(data_dir, 'employees.csv')
    if not os.path.exists(file_path):
        print(f"警告: 找不到员工数据文件 {file_path}")
        return
    
    try:
        df = pd.read_csv(file_path)
        
        # 先把原始 EmployeeID 列值存入临时变量
        employee_id_values = df['EmployeeID'].values
        
        # 重命名ID列为 Neo4j Admin 导入格式的主键标识
        df = df.rename(columns={'EmployeeID': 'employeeId:ID(Employee)'})
        
        # rename 完成后再写回同名普通属性列，使 Cypher WHERE e.EmployeeID = x 可正常执行
        df['EmployeeID'] = employee_id_values
        
        # 添加标签列
        df['labels:LABEL'] = 'Employee'
        
        # 保存为Neo4j Admin导入格式
        output_file = os.path.join(output_dir, 'employee_nodes.csv')
        df.to_csv(output_file, index=False)
        print(f"员工节点文件已保存: {output_file}")
    except Exception as e:
        print(f"处理员工节点时出错: {e}")

def prepare_shipper_nodes(data_dir, output_dir):
    """准备物流公司节点文件"""
    file_path = os.path.join(data_dir, 'shippers.csv')
    if not os.path.exists(file_path):
        print(f"警告: 找不到物流公司数据文件 {file_path}")
        return
    
    try:
        df = pd.read_csv(file_path)
        
        # 先把原始 ShipperID 列值存入临时变量
        shipper_id_values = df['ShipperID'].values
        
        # 重命名ID列为 Neo4j Admin 导入格式的主键标识
        df = df.rename(columns={'ShipperID': 'shipperId:ID(Shipper)'})
        
        # rename 完成后再写回同名普通属性列，使 Cypher WHERE s.ShipperID = x 可正常执行
        df['ShipperID'] = shipper_id_values
        
        # 添加标签列
        df['labels:LABEL'] = 'Shipper'
        
        # 保存为Neo4j Admin导入格式
        output_file = os.path.join(output_dir, 'shipper_nodes.csv')
        df.to_csv(output_file, index=False)
        print(f"物流公司节点文件已保存: {output_file}")
    except Exception as e:
        print(f"处理物流公司节点时出错: {e}")

def prepare_order_nodes(data_dir, output_dir):
    """准备订单节点文件"""
    file_path = os.path.join(data_dir, 'orders.csv')
    if not os.path.exists(file_path):
        print(f"警告: 找不到订单数据文件 {file_path}")
        return
    
    try:
        df = pd.read_csv(file_path)
        
        # 关键修复：先把原始 OrderID 列值存入临时变量
        # rename 之后 'OrderID' 成为 Neo4j 内部主键标识（:ID列），不再作为普通属性存储
        order_id_values = df['OrderID'].values
        
        # 重命名ID列为 Neo4j Admin 导入格式的主键标识
        df = df.rename(columns={'OrderID': 'orderId:ID(Order)'})
        
        # rename 完成后再写回同名普通属性列，使 Cypher WHERE o.OrderID = 1001 可正常执行
        df['OrderID'] = order_id_values
        
        # 添加标签列
        df['labels:LABEL'] = 'Order'
        
        # 移除外键关系列（这些数据已通过边文件建立关系，节点本身不需要保留）
        cols_to_drop = ['CustomerID', 'EmployeeID', 'ShipVia',
                        # 移除 SQL JOIN 带入的冗余字段，这些信息应通过图关系访问，而非直接存在节点上
                        'CustomerName', 'LastName', 'FirstName', 'ShipperName']
        df = df.drop(columns=[c for c in cols_to_drop if c in df.columns])
        
        # 保存为Neo4j Admin导入格式
        output_file = os.path.join(output_dir, 'order_nodes.csv')
        df.to_csv(output_file, index=False)
        print(f"订单节点文件已保存: {output_file}")
    except Exception as e:
        print(f"处理订单节点时出错: {e}")

def prepare_review_nodes(data_dir, output_dir):
    """准备评论节点文件"""
    file_path = os.path.join(data_dir, 'reviews.csv')
    if not os.path.exists(file_path):
        print(f"警告: 找不到评论数据文件 {file_path}")
        return
    
    try:
        df = pd.read_csv(file_path)
        
        # 先把原始 ReviewID 列值存入临时变量
        review_id_values = df['ReviewID'].values
        
        # 重命名ID列为 Neo4j Admin 导入格式的主键标识
        df = df.rename(columns={'ReviewID': 'reviewId:ID(Review)'})
        
        # rename 完成后再写回同名普通属性列，使 Cypher WHERE r.ReviewID = x 可正常执行
        df['ReviewID'] = review_id_values
        
        # 添加标签列
        df['labels:LABEL'] = 'Review'
        
        # 移除外键关系列（已在边文件中建立 WROTE/ABOUT 关系）
        # 同时移除 SQL JOIN 带入的冗余字段（ProductName/CustomerName/CategoryName 应通过关系遍历获取）
        cols_to_drop = ['ProductID', 'CustomerID', 'ProductName', 'CustomerName', 'CategoryName']
        df = df.drop(columns=[c for c in cols_to_drop if c in df.columns])
        
        # 保存为Neo4j Admin导入格式
        output_file = os.path.join(output_dir, 'review_nodes.csv')
        df.to_csv(output_file, index=False)
        print(f"评论节点文件已保存: {output_file}")
    except Exception as e:
        print(f"处理评论节点时出错: {e}")

def prepare_product_category_edges(data_dir, output_dir):
    """准备产品-类别关系边文件"""
    file_path = os.path.join(data_dir, 'products.csv')
    if not os.path.exists(file_path):
        print(f"警告: 找不到产品数据文件 {file_path}")
        return
    
    try:
        df = pd.read_csv(file_path)
        if 'ProductID' not in df.columns or 'CategoryID' not in df.columns:
            print("警告: 产品数据缺少ProductID或CategoryID列")
            return
        
        # 创建边数据框
        edges_df = pd.DataFrame({
            ':START_ID(Product)': df['ProductID'],
            ':END_ID(Category)': df['CategoryID'],
            ':TYPE': 'BELONGS_TO'
        })
        
        # 保存为Neo4j Admin导入格式
        output_file = os.path.join(output_dir, 'product_category_edges.csv')
        edges_df.to_csv(output_file, index=False)
        print(f"产品-类别关系边文件已保存: {output_file}")
    except Exception as e:
        print(f"处理产品-类别关系边时出错: {e}")

def prepare_product_supplier_edges(data_dir, output_dir):
    """准备产品-供应商关系边文件"""
    file_path = os.path.join(data_dir, 'products.csv')
    if not os.path.exists(file_path):
        print(f"警告: 找不到产品数据文件 {file_path}")
        return
    
    try:
        df = pd.read_csv(file_path)
        if 'ProductID' not in df.columns or 'SupplierID' not in df.columns:
            print("警告: 产品数据缺少ProductID或SupplierID列")
            return
        
        # 创建边数据框
        edges_df = pd.DataFrame({
            ':START_ID(Product)': df['ProductID'],
            ':END_ID(Supplier)': df['SupplierID'],
            ':TYPE': 'SUPPLIED_BY'
        })
        
        # 保存为Neo4j Admin导入格式
        output_file = os.path.join(output_dir, 'product_supplier_edges.csv')
        edges_df.to_csv(output_file, index=False)
        print(f"产品-供应商关系边文件已保存: {output_file}")
    except Exception as e:
        print(f"处理产品-供应商关系边时出错: {e}")

def prepare_customer_order_edges(data_dir, output_dir):
    """准备客户-订单关系边文件"""
    file_path = os.path.join(data_dir, 'orders.csv')
    if not os.path.exists(file_path):
        print(f"警告: 找不到订单数据文件 {file_path}")
        return
    
    try:
        df = pd.read_csv(file_path)
        if 'CustomerID' not in df.columns or 'OrderID' not in df.columns:
            print("警告: 订单数据缺少CustomerID或OrderID列")
            return
        
        # 创建边数据框
        edges_df = pd.DataFrame({
            ':START_ID(Customer)': df['CustomerID'],
            ':END_ID(Order)': df['OrderID'],
            ':TYPE': 'PLACED'
        })
        
        # 保存为Neo4j Admin导入格式
        output_file = os.path.join(output_dir, 'customer_order_edges.csv')
        edges_df.to_csv(output_file, index=False)
        print(f"客户-订单关系边文件已保存: {output_file}")
    except Exception as e:
        print(f"处理客户-订单关系边时出错: {e}")

def prepare_employee_order_edges(data_dir, output_dir):
    """准备员工-订单关系边文件"""
    file_path = os.path.join(data_dir, 'orders.csv')
    if not os.path.exists(file_path):
        print(f"警告: 找不到订单数据文件 {file_path}")
        return
    
    try:
        df = pd.read_csv(file_path)
        if 'EmployeeID' not in df.columns or 'OrderID' not in df.columns:
            print("警告: 订单数据缺少EmployeeID或OrderID列")
            return
        
        # 创建边数据框
        edges_df = pd.DataFrame({
            ':START_ID(Employee)': df['EmployeeID'],
            ':END_ID(Order)': df['OrderID'],
            ':TYPE': 'PROCESSED'
        })
        
        # 保存为Neo4j Admin导入格式
        output_file = os.path.join(output_dir, 'employee_order_edges.csv')
        edges_df.to_csv(output_file, index=False)
        print(f"员工-订单关系边文件已保存: {output_file}")
    except Exception as e:
        print(f"处理员工-订单关系边时出错: {e}")

def prepare_order_shipper_edges(data_dir, output_dir):
    """准备订单-物流公司关系边文件"""
    file_path = os.path.join(data_dir, 'orders.csv')
    if not os.path.exists(file_path):
        print(f"警告: 找不到订单数据文件 {file_path}")
        return
    
    try:
        df = pd.read_csv(file_path)
        if 'OrderID' not in df.columns or 'ShipVia' not in df.columns:
            print("警告: 订单数据缺少OrderID或ShipVia列")
            return
        
        # 创建边数据框
        edges_df = pd.DataFrame({
            ':START_ID(Order)': df['OrderID'],
            ':END_ID(Shipper)': df['ShipVia'],
            ':TYPE': 'SHIPPED_VIA'
        })
        
        # 保存为Neo4j Admin导入格式
        output_file = os.path.join(output_dir, 'order_shipper_edges.csv')
        edges_df.to_csv(output_file, index=False)
        print(f"订单-物流公司关系边文件已保存: {output_file}")
    except Exception as e:
        print(f"处理订单-物流公司关系边时出错: {e}")

def prepare_order_product_edges(data_dir, output_dir):
    """准备订单-产品关系边文件"""
    file_path = os.path.join(data_dir, 'order_details.csv')
    if not os.path.exists(file_path):
        print(f"警告: 找不到订单详情数据文件 {file_path}")
        return
    
    try:
        df = pd.read_csv(file_path)
        if 'OrderID' not in df.columns or 'ProductID' not in df.columns:
            print("警告: 订单详情数据缺少OrderID或ProductID列")
            return
        
        # 创建边数据框
        edges_df = pd.DataFrame({
            ':START_ID(Order)': df['OrderID'],
            ':END_ID(Product)': df['ProductID'],
            ':TYPE': 'CONTAINS',
            'UnitPrice': df['UnitPrice'],
            'Quantity': df['Quantity'],
            'Discount': df['Discount']
        })
        
        # 保存为Neo4j Admin导入格式
        output_file = os.path.join(output_dir, 'order_product_edges.csv')
        edges_df.to_csv(output_file, index=False)
        print(f"订单-产品关系边文件已保存: {output_file}")
    except Exception as e:
        print(f"处理订单-产品关系边时出错: {e}")

def prepare_employee_reports_to_edges(data_dir, output_dir):
    """准备员工-上级关系边文件"""
    file_path = os.path.join(data_dir, 'employees.csv')
    if not os.path.exists(file_path):
        print(f"警告: 找不到员工数据文件 {file_path}")
        return
    
    try:
        df = pd.read_csv(file_path)
        if 'EmployeeID' not in df.columns or 'ReportsTo' not in df.columns:
            print("警告: 员工数据缺少EmployeeID或ReportsTo列")
            return
        
        # 过滤掉ReportsTo为空的行
        df = df.dropna(subset=['ReportsTo'])
        
        # 关键修复：ReportsTo 列因含有 NaN 行，pandas 会将其自动升格为 float64。
        # dropna 后数值虽已有效，但仍以 "1.0" 而非 "1" 形式写入 CSV，导致
        # neo4j-admin import 无法将浮点型 END_ID 与整数型节点主键匹配，
        # 配合 --skip-bad-relationships=true 时静默丢弃所有 REPORTS_TO 关系。
        # 强制转为 int64 即可修复。
        df = df.copy()  # 避免 SettingWithCopyWarning
        df['ReportsTo'] = df['ReportsTo'].astype(int)
        
        # 创建边数据框
        edges_df = pd.DataFrame({
            ':START_ID(Employee)': df['EmployeeID'],
            ':END_ID(Employee)': df['ReportsTo'],
            ':TYPE': 'REPORTS_TO'
        })
        
        # 保存为Neo4j Admin导入格式
        output_file = os.path.join(output_dir, 'employee_reports_to_edges.csv')
        edges_df.to_csv(output_file, index=False)
        print(f"员工-上级关系边文件已保存: {output_file}")
    except Exception as e:
        print(f"处理员工-上级关系边时出错: {e}")

def prepare_review_edges(data_dir, output_dir):
    """准备评论关系边文件"""
    file_path = os.path.join(data_dir, 'reviews.csv')
    if not os.path.exists(file_path):
        print(f"警告: 找不到评论数据文件 {file_path}")
        return
    
    try:
        df = pd.read_csv(file_path)
        
        # 1. 客户-评论关系
        if 'CustomerID' in df.columns and 'ReviewID' in df.columns:
            customer_review_edges = pd.DataFrame({
                ':START_ID(Customer)': df['CustomerID'],
                ':END_ID(Review)': df['ReviewID'],
                ':TYPE': 'WROTE'
            })
            
            output_file = os.path.join(output_dir, 'customer_review_edges.csv')
            customer_review_edges.to_csv(output_file, index=False)
            print(f"客户-评论关系边文件已保存: {output_file}")
        
        # 2. 评论-产品关系
        if 'ReviewID' in df.columns and 'ProductID' in df.columns:
            review_product_edges = pd.DataFrame({
                ':START_ID(Review)': df['ReviewID'],
                ':END_ID(Product)': df['ProductID'],
                ':TYPE': 'ABOUT'
            })
            
            output_file = os.path.join(output_dir, 'review_product_edges.csv')
            review_product_edges.to_csv(output_file, index=False)
            print(f"评论-产品关系边文件已保存: {output_file}")
        
    except Exception as e:
        print(f"处理评论关系边时出错: {e}")

def generate_import_command(output_dir):
    """生成Neo4j Admin导入命令（适用于Neo4j 2025.02.0及更高版本）"""
    command_path = os.path.join(output_dir, 'import_command.bat')
    
    with open(command_path, 'w') as f:
        f.write("@echo off\n\n")
        f.write("REM Neo4j Admin导入命令\n")
        f.write("REM 适用于Neo4j 2025.02.0及更高版本\n")
        f.write("REM 生成时间: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n\n")
        
        f.write("neo4j-admin database import full neo4j --overwrite-destination ^\n")
        f.write(f"  --nodes=Product=\"{os.path.abspath(os.path.join(output_dir, 'product_nodes.csv'))}\" ^\n")
        f.write(f"  --nodes=Category=\"{os.path.abspath(os.path.join(output_dir, 'category_nodes.csv'))}\" ^\n")
        f.write(f"  --nodes=Supplier=\"{os.path.abspath(os.path.join(output_dir, 'supplier_nodes.csv'))}\" ^\n")
        f.write(f"  --nodes=Customer=\"{os.path.abspath(os.path.join(output_dir, 'customer_nodes.csv'))}\" ^\n")
        f.write(f"  --nodes=Employee=\"{os.path.abspath(os.path.join(output_dir, 'employee_nodes.csv'))}\" ^\n")
        f.write(f"  --nodes=Shipper=\"{os.path.abspath(os.path.join(output_dir, 'shipper_nodes.csv'))}\" ^\n")
        f.write(f"  --nodes=Order=\"{os.path.abspath(os.path.join(output_dir, 'order_nodes.csv'))}\" ^\n")
        f.write(f"  --nodes=Review=\"{os.path.abspath(os.path.join(output_dir, 'review_nodes.csv'))}\" ^\n")
        f.write(f"  --relationships=BELONGS_TO=\"{os.path.abspath(os.path.join(output_dir, 'product_category_edges.csv'))}\" ^\n")
        f.write(f"  --relationships=SUPPLIED_BY=\"{os.path.abspath(os.path.join(output_dir, 'product_supplier_edges.csv'))}\" ^\n")
        f.write(f"  --relationships=PLACED=\"{os.path.abspath(os.path.join(output_dir, 'customer_order_edges.csv'))}\" ^\n")
        f.write(f"  --relationships=PROCESSED=\"{os.path.abspath(os.path.join(output_dir, 'employee_order_edges.csv'))}\" ^\n")
        f.write(f"  --relationships=SHIPPED_VIA=\"{os.path.abspath(os.path.join(output_dir, 'order_shipper_edges.csv'))}\" ^\n")
        f.write(f"  --relationships=CONTAINS=\"{os.path.abspath(os.path.join(output_dir, 'order_product_edges.csv'))}\" ^\n")
        f.write(f"  --relationships=REPORTS_TO=\"{os.path.abspath(os.path.join(output_dir, 'employee_reports_to_edges.csv'))}\" ^\n")
        f.write(f"  --relationships=WROTE=\"{os.path.abspath(os.path.join(output_dir, 'customer_review_edges.csv'))}\" ^\n")
        f.write(f"  --relationships=ABOUT=\"{os.path.abspath(os.path.join(output_dir, 'review_product_edges.csv'))}\" ^\n")
        f.write("  --delimiter=\",\" ^\n")
        f.write("  --array-delimiter=\";\" ^\n")
        f.write("  --skip-bad-relationships=true ^\n")
        f.write("  --skip-duplicate-nodes=true\n")
    
    print(f"Neo4j Admin导入命令(适用于Neo4j 2025.02.0及更高版本)已保存: {command_path}")

if __name__ == "__main__":
    # 获取脚本所在的绝对路径作为基准，避免因执行目录不同导致找不到文件
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, 'exported_data')
    output_dir = os.path.join(script_dir, 'data', 'neo4j_admin')
    
    # 使用绝对路径执行处理
    prepare_neo4j_admin_import(data_dir=data_dir, output_dir=output_dir)