import pandas as pd
import db

def process_excel_import(file_path):
    """엑셀 또는 CSV 파일을 읽고 검증한 뒤 DB에 대량 등록하는 비즈니스 로직"""
    if not file_path:
        return False, "파일 경로가 선택되지 않았습니다."

    try:
        # 파일 형식에 따라 판다스로 읽기
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)

        # 필수 컬럼 검증
        required_columns = ['품명', '조달단가', '보유수량']
        for col in required_columns:
            if col not in df.columns:
                return False, f"엑셀 파일에 필수 열('{col}')이 존재하지 않습니다.\n양식을 확인해주세요."

        # 데이터 가공 및 타입 변환
        item_list = []
        for _, row in df.iterrows():
            name = str(row['품명']).strip()
            price = int(row['조달단가'])
            stock = int(row['보유수량'])
            item_list.append((name, price, stock))

        if not item_list:
            return False, "엑셀 파일에 등록할 데이터가 존재하지 않습니다."

        # DB 대량 삽입 함수 호출
        db.insert_items_bulk(item_list)
        return True, f"총 {len(item_list)}건의 물자가 성공적으로 등록되었습니다."

    except Exception as e:
        return False, f"파일을 처리하는 중 에러가 발생했습니다:\n{str(e)}"