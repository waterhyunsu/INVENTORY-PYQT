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

        # 필수 컬럼에 '재고번호 (NSN)' 추가
        required_columns = ['재고번호 (NSN)', '품명', '조달단가', '보유수량']
        for col in required_columns:
            if col not in df.columns:
                return False, f"엑셀 파일에 필수 열('{col}')이 존재하지 않습니다.\n양식을 확인해주세요."

        # 데이터 가공 및 타입 변환
        item_list = []
        for _, row in df.iterrows():
            # 엑셀의 한국어 컬럼명을 읽어와서 nsn, name, price, stock 추출
            nsn = str(row['재고번호 (NSN)']).strip()
            name = str(row['품명']).strip()
            price = int(row['조달단가'])
            stock = int(row['보유수량'])
            
            item_list.append((nsn, name, price, stock))

        if not item_list:
            return False, "엑셀 파일에 등록할 데이터가 존재하지 않습니다."

        # DB 대량 삽입 함수 호출
        db.insert_items_bulk(item_list)
        return True, f"총 {len(item_list)}건의 물자가 성공적으로 등록되었습니다."

    except Exception as e:
        return False, f"파일을 처리하는 중 에러가 발생했습니다:\n{str(e)}"

def export_excel(file_path):
    """DB의 전체 물자 데이터를 읽어 엑셀 파일로 내보내는 비즈니스 로직"""
    if not file_path:
        return False, "저장할 파일 경로가 선택되지 않았습니다."

    try:
        # db 모듈을 통해 전체 데이터 조회
        rows = db.get_all_items()
        if not rows:
            return False, "내보낼 데이터가 존재하지 않습니다."

        # 판다스 DataFrame으로 변환 (컬럼명 맞춤)
        df = pd.DataFrame(rows, columns=['재고번호 (NSN)', '품명', '조달단가', '보유수량'])

        # 파일 확장자에 따라 저장 (csv 또는 xlsx)
        if file_path.endswith('.csv'):
            df.to_csv(file_path, index=False, encoding='utf-8-sig')
        else:
            df.to_excel(file_path, index=False)

        return True, f"총 {len(rows)}건의 데이터가 성공적으로 내보내기 되었습니다."

    except Exception as e:
        return False, f"엑셀 내보내기 중 에러가 발생했습니다:\n{str(e)}"