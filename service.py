import pandas as pd
import db

def process_excel_import(file_path):
    """엑셀 또는 CSV 파일을 읽고 검증한 뒤 DB에 대량 등록하는 비즈니스 로직 (중복 품목 수량 합산 기능 포함)"""
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

        # 동일한 재고번호 및 품명별로 수량을 누적하기 위한 딕셔너리(Map) 활용
        aggregated_items = {}

        for _, row in df.iterrows():
            nsn = str(row['재고번호 (NSN)']).strip()
            name = str(row['품명']).strip()
            
            try:
                price = int(row['조달단가'])
                stock = int(row['보유수량'])
            except ValueError:
                return False, f"단가 또는 수량에 숫자가 아닌 값이 포함되어 있습니다.\n(NSN: {nsn}, 품명: {name})"

            # 고유 키 (재고번호와 품명이 모두 같으면 같은 품목으로 취급)
            key = (nsn, name)

            if key in aggregated_items:
                # 이미 존재하는 품목이면 보유수량을 누적 합산 (단가는 최신 값 또는 기존 값 유지)
                aggregated_items[key]['stock'] += stock
                # 단가는 필요에 따라 최신 행의 단가로 갱신하거나 유지할 수 있습니다. (여기서는 최신 단가 반영)
                aggregated_items[key]['price'] = price 
            else:
                # 신규 품목 등록
                aggregated_items[key] = {
                    'price': price,
                    'stock': stock
                }

        # 딕셔너리 형태를 기존 DB 연동용 튜플 리스트로 변환
        item_list = []
        for (nsn, name), data in aggregated_items.items():
            item_list.append((nsn, name, data['price'], data['stock']))

        if not item_list:
            return False, "엑셀 파일에 등록할 데이터가 존재하지 않습니다."

        # DB 대량 삽입 함수 호출
        db.insert_items_bulk(item_list)
        return True, f"중복 합산 처리가 완료되어, 총 {len(item_list)}개의 고유 품목(합산 반영)이 성공적으로 등록되었습니다."

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