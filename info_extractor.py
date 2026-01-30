import re
import pandas as pd
import streamlit as st
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows

# 初始化会话状态
if 'data_list' not in st.session_state:
    st.session_state.data_list = []
if 'input_text' not in st.session_state:
    st.session_state.input_text = ""

def extract_info(text):
    """
    从文本中提取关键信息：
    1. 身份证兼容「身份证号码：」「身份证：」两种格式
    2. 手机号兼容「手机号：」「电话号码：」「手机：」三种格式
    3. 价格优先级：价格 > 初始价格 > 初始价（均无则为空）
    4. 备注保留所有未被核心字段提取的内容
    """
    result = {
        '姓名': '',
        '身份证号': '',
        '手机号': '',
        '名称': '',
        '价格': '',
        '备注': ''
    }
    
    # 保存原始文本（用于价格兜底提取）
    original_text = text.strip()
    lines = [line.strip() for line in original_text.split('\n') if line.strip()]
    extracted_lines = []

    # 1. 提取姓名
    name_pattern = re.compile(r'^姓名：.*', re.M)
    for i, line in enumerate(lines):
        if re.match(name_pattern, line):
            name_match = re.search(r'姓名：([^\n]+)', line)
            if name_match:
                result['姓名'] = name_match.group(1).strip()
                extracted_lines.append(i)
            break

    # 2. 提取身份证号码（兼容「身份证号码：」「身份证：」两种格式）
    id_card_patterns = [
        re.compile(r'^身份证号码：.*', re.M),
        re.compile(r'^身份证：.*', re.M)
    ]
    id_card_extracted = False
    for pattern in id_card_patterns:
        if id_card_extracted:
            break
        for i, line in enumerate(lines):
            if re.match(pattern, line):
                # 提取18位身份证号（支持数字+X/x）
                id_card_match = re.search(r'(\d{18}|\d{17}X|\d{17}x)', line)
                if id_card_match:
                    result['身份证号'] = id_card_match.group(1).strip()
                    extracted_lines.append(i)
                    id_card_extracted = True
                break

    # 3. 提取手机号（兼容「手机号：」「电话号码：」「手机：」三种格式）
    phone_patterns = [
        re.compile(r'^手机号：.*', re.M),       # 优先级1
        re.compile(r'^电话号码：.*', re.M),   # 优先级2
        re.compile(r'^手机：.*', re.M)        # 优先级3
    ]
    phone_extracted = False
    for pattern in phone_patterns:
        if phone_extracted:
            break
        for i, line in enumerate(lines):
            if re.match(pattern, line):
                # 提取11位数字（仅保留有效手机号）
                phone_match = re.search(r'(\d{11})', line)
                if phone_match:
                    result['手机号'] = phone_match.group(1).strip()
                    extracted_lines.append(i)
                    phone_extracted = True
                break

    # 4. 提取名称
    name_product_pattern = re.compile(r'^名称：.*', re.M)
    for i, line in enumerate(lines):
        if re.match(name_product_pattern, line):
            name_product_match = re.search(r'名称：([^\n]+)', line)
            if name_product_match:
                result['名称'] = name_product_match.group(1).strip()
                extracted_lines.append(i)
            break

    # 5. 提取价格（兜底支持「初始价格：」「初始价：」）
    price_extracted = False
    # 第一步：优先提取「价格：xxx」
    price_pattern = re.compile(r'^价格：.*', re.M)
    for i, line in enumerate(lines):
        if re.match(price_pattern, line):
            price_match = re.search(r'价格：([^\n]+)', line)
            if price_match:
                price_text = price_match.group(1).strip()
                pure_price = re.search(r'(\d+\.?\d*)', price_text)
                if pure_price:
                    result['价格'] = pure_price.group(1)
                    price_extracted = True
                else:
                    result['价格'] = price_text
                extracted_lines.append(i)
            break
    
    # 第二步：若未提取到价格，依次匹配「初始价格：xxx」「初始价：xxx」兜底
    if not price_extracted:
        # 先匹配「初始价格：」
        initial_price_match = re.search(r'初始价格：([^\n]+)', original_text)
        if initial_price_match:
            initial_price_text = initial_price_match.group(1).strip()
            pure_initial_price = re.search(r'(\d+\.?\d*)', initial_price_text)
            if pure_initial_price:
                result['价格'] = pure_initial_price.group(1)
        else:
            # 再匹配「初始价：」
            initial_price_short_match = re.search(r'初始价：([^\n]+)', original_text)
            if initial_price_short_match:
                initial_price_short_text = initial_price_short_match.group(1).strip()
                pure_initial_price_short = re.search(r'(\d+\.?\d*)', initial_price_short_text)
                if pure_initial_price_short:
                    result['价格'] = pure_initial_price_short.group(1)

    # 6. 处理备注：保留所有未被核心字段提取的行
    remaining_lines = [lines[i] for i in range(len(lines)) if i not in extracted_lines]
    result['备注'] = '\n'.join(remaining_lines)
    
    return result

def generate_excel_with_column_width(df, column_width=20):
    wb = Workbook()
    ws = wb.active
    ws.title = "信息提取结果"
    for r in dataframe_to_rows(df, index=False, header=True):
        ws.append(r)
    for column in ws.columns:
        column_letter = column[0].column_letter
        ws.column_dimensions[column_letter].width = column_width
    import io
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output.getvalue()

# 新增：删除单条数据的函数
def delete_single_data(index):
    """根据索引删除指定行数据"""
    if 0 <= index < len(st.session_state.data_list):
        del st.session_state.data_list[index]
        st.success(f'第{index+1}条数据已成功删除！')
    else:
        st.warning('数据索引无效，删除失败！')

def main():
    st.title('文本信息提取工具（支持单条删除+多次累积）')
    st.markdown('---')
    
    # 文本输入框：移除示例、占位符改为「请输入文本」
    st.session_state.input_text = st.text_area(
        '请输入需要提取信息的文本',
        value=st.session_state.input_text,
        height=300,
        placeholder='请输入文本'
    )
    
    # 按钮区域：提取添加 + 清空文本
    col1, col2 = st.columns(2)
    with col1:
        # 提取并添加到表格按钮
        if st.button('提取信息并添加到表格', type='primary'):
            if not st.session_state.input_text.strip():
                st.warning('请输入需要提取的文本内容！')
            else:
                # 提取信息
                info = extract_info(st.session_state.input_text)
                # 添加到会话状态的列表中
                st.session_state.data_list.append(info)
                st.success('信息已成功添加到表格！')
    
    with col2:
        # 清空填写文本按钮
        if st.button('清空填写文本', type='secondary'):
            st.session_state.input_text = ""
            st.success('输入框文本已清空！')
    
    # 清空所有表格数据按钮
    col3 = st.columns(1)[0]
    with col3:
        if st.button('清空所有表格数据', type='secondary'):
            st.session_state.data_list = []
            st.warning('所有表格数据已清空！')
    
    st.markdown('---')
    
    # 展示累积的表格（支持单条删除）
    if st.session_state.data_list:
        st.subheader('累积提取结果（支持单条删除）')
        # 转换为DataFrame并重置索引（用于行号显示）
        df = pd.DataFrame(st.session_state.data_list).reset_index(drop=True)
        
        # 遍历每条数据，生成带删除按钮的行
        for idx in range(len(df)):
            # 定义每行的列布局：数据列 + 操作列
            # 动态调整列宽，适配备注字段
            data_cols = st.columns(len(df.columns))
            btn_col = st.columns(1)
            
            # 显示当前行的所有数据
            for col_idx, col_name in enumerate(df.columns):
                with data_cols[col_idx]:
                    # 备注字段换行显示，其他字段正常显示
                    if col_name == '备注' and df.iloc[idx][col_name]:
                        st.write(f'**{col_name}：**\n{df.iloc[idx][col_name]}')
                    else:
                        st.write(f'**{col_name}：** {df.iloc[idx][col_name] if df.iloc[idx][col_name] else "-"}')
            
            # 显示当前行的删除按钮
            with btn_col[0]:
                delete_btn = st.button(
                    f'删除第{idx+1}条',
                    key=f'delete_{idx}',  # 唯一key，避免按钮冲突
                    type='secondary'
                )
                # 点击按钮触发删除
                if delete_btn:
                    delete_single_data(idx)
                    # 刷新页面，立即显示删除后的结果
                    st.rerun()
            
            # 行分隔线，区分不同数据
            st.markdown('---')
        
        # 生成带列宽的Excel文件（排除无实际意义的索引）
        raw_df = pd.DataFrame(st.session_state.data_list)
        excel_data = generate_excel_with_column_width(raw_df, column_width=20)
        
        # 下载按钮
        st.download_button(
            label='下载完整Excel表格',
            data=excel_data,
            file_name='信息提取累积结果.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            type='primary'
        )
    else:
        st.info('暂无提取数据，请输入文本并点击「提取信息并添加到表格」按钮')

if __name__ == '__main__':
    main()
