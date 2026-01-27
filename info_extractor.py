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
    result = {
        '姓名': '',
        '身份证号': '',
        '手机号': '',
        '名称': '',
        '价格': '',
        '备注': ''
    }
    lines = [line.strip() for line in text.strip().split('\n') if line.strip()]
    extracted_lines = []

    # 提取姓名
    name_pattern = re.compile(r'^姓名：.*', re.M)
    for i, line in enumerate(lines):
        if re.match(name_pattern, line):
            name_match = re.search(r'姓名：([^\n]+)', line)
            if name_match:
                result['姓名'] = name_match.group(1).strip()
                extracted_lines.append(i)
            break

    # 提取身份证号
    id_card_pattern = re.compile(r'^身份证号码：.*', re.M)
    for i, line in enumerate(lines):
        if re.match(id_card_pattern, line):
            id_card_match = re.search(r'身份证号码：(\d{18}|\d{17}X|\d{17}x)', line)
            if id_card_match:
                result['身份证号'] = id_card_match.group(1).strip()
                extracted_lines.append(i)
            break

    # 提取手机号
    phone_pattern = re.compile(r'^手机号：.*', re.M)
    for i, line in enumerate(lines):
        if re.match(phone_pattern, line):
            phone_match = re.search(r'手机号：(\d{11})', line)
            if phone_match:
                result['手机号'] = phone_match.group(1).strip()
                extracted_lines.append(i)
            break

    # 提取名称
    name_product_pattern = re.compile(r'^名称：.*', re.M)
    for i, line in enumerate(lines):
        if re.match(name_product_pattern, line):
            name_product_match = re.search(r'名称：([^\n]+)', line)
            if name_product_match:
                result['名称'] = name_product_match.group(1).strip()
                extracted_lines.append(i)
            break

    # 提取价格（仅保留数字）
    price_pattern = re.compile(r'^价格：.*', re.M)
    for i, line in enumerate(lines):
        if re.match(price_pattern, line):
            price_match = re.search(r'价格：([^\n]+)', line)
            if price_match:
                price_text = price_match.group(1).strip()
                pure_price = re.search(r'(\d+\.?\d*)', price_text)
                if pure_price:
                    result['价格'] = pure_price.group(1)
                else:
                    result['价格'] = price_text
                extracted_lines.append(i)
            break

    # 处理备注
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

def main():
    st.title('文本信息提取工具（支持多次累积）')
    st.markdown('---')
    st.session_state.input_text = st.text_area(
        '请输入需要提取信息的文本',
        value=st.session_state.input_text,
        height=300,
        placeholder='例如：\n姓名：杜翠英\n身份证号码：412724196809296542\n手机号：15896756230\n名称：美的空调\n价格：8999元\n品牌：美的   类别：空调\n初始价格：8999元\n补贴金额：1349.85元\n实付金额：7649.15元'
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button('提取信息并添加到表格', type='primary'):
            if not st.session_state.input_text.strip():
                st.warning('请输入需要提取的文本内容！')
            else:
                info = extract_info(st.session_state.input_text)
                st.session_state.data_list.append(info)
                st.success('信息已成功添加到表格！')
    with col2:
        if st.button('清空填写文本', type='secondary'):
            st.session_state.input_text = ""
            st.success('输入框文本已清空！')

    col3 = st.columns(1)[0]
    with col3:
        if st.button('清空所有表格数据', type='secondary'):
            st.session_state.data_list = []
            st.warning('所有表格数据已清空！')

    st.markdown('---')
    if st.session_state.data_list:
        st.subheader('累积提取结果')
        df = pd.DataFrame(st.session_state.data_list)
        st.dataframe(df, use_container_width=True)
        excel_data = generate_excel_with_column_width(df, column_width=20)
        st.download_button(
            label='下载完整Excel表格',
            data=excel_data,
            file_name='信息提取累积结果.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    else:
        st.info('暂无提取数据，请输入文本并点击「提取信息并添加到表格」按钮')

if __name__ == '__main__':
    main()
