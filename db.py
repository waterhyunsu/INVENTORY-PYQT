import pymysql

# MySQL 접속 설정 변수 정의
DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASSWORD = '1234'
DB_NAME = 'delis_db'
DB_PORT = 3306

def get_connection():
    """DB 커넥션 객체 생성 함수"""
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=DB_PORT,
        charset='utf8mb4'
    )

def init_history_db():
    """이력 테이블이 없으면 생성 (MySQL 버전)"""
    conn = get_connection()
    with conn.cursor() as cursor:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                user_id VARCHAR(50),
                nsn VARCHAR(50),
                item_name VARCHAR(100),
                action_type VARCHAR(20),
                qty_change INT,
                current_stock INT
            );
        ''')
        conn.commit()
    conn.close()

def log_history(user_id, nsn, item_name, action_type, qty_change, current_stock):
    """작업 이력 남기기"""
    conn = get_connection()
    with conn.cursor() as cursor:
        query = """
            INSERT INTO history (user_id, nsn, item_name, action_type, qty_change, current_stock)
            VALUES (%s, %s, %s, %s, %s, %s);
        """
        cursor.execute(query, (user_id, nsn, item_name, action_type, qty_change, current_stock))
        conn.commit()
    conn.close()

def get_all_history():
    """모든 이력 조회 (최신순)"""
    conn = get_connection()
    with conn.cursor() as cursor:
        query = """
            SELECT timestamp, user_id, nsn, item_name, action_type, qty_change, current_stock
            FROM history
            ORDER BY id DESC;
        """
        cursor.execute(query)
        result = cursor.fetchall()
    conn.close()
    return result

def get_all_items():
    """재고 목록 전체 조회 (Read)"""
    conn = get_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT nsn, name, price, stock FROM item;")
        result = cursor.fetchall()
    conn.close()
    return result

def insert_item(nsn, name, price, stock):
    """신규 물자 추가 (Create) - nsn 포함 수정"""
    conn = get_connection()
    with conn.cursor() as cursor:
        query = "INSERT INTO item (nsn, name, price, stock) VALUES (%s, %s, %s, %s);"
        cursor.execute(query, (nsn, name, price, stock))
        conn.commit()
    conn.close()

def update_item(nsn, name, price, stock):
    conn = get_connection()
    with conn.cursor() as cursor:
        cursor.execute("""
            UPDATE item 
            SET name = %s, price = %s, stock = %s 
            WHERE nsn = %s
        """, (name, price, stock, nsn))
        conn.commit()
    conn.close()

def consume_stock(nsn, consume_qty):
    """특정 수량만큼 재고 차감 (소모 처리)"""
    conn = get_connection()
    with conn.cursor() as cursor:
        # 1. 현재고 확인 (초과 소모 방지)
        cursor.execute("SELECT stock FROM item WHERE nsn = %s;", (nsn,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            raise Exception("해당 물자를 찾을 수 없습니다.")
        
        current_stock = row[0]
        if current_stock < consume_qty:
            conn.close()
            raise Exception(f"현재 보유 수량({current_stock} EA)보다 많은 수량을 소모할 수 없습니다.")
        
        # 2. 재고 차감 쿼리 실행 (UPDATE)
        query = "UPDATE item SET stock = stock - %s WHERE nsn = %s;"
        cursor.execute(query, (consume_qty, nsn))
        conn.commit()
    conn.close()

def check_login(user_id, password):
    """사용자 아이디와 비밀번호 확인"""
    conn = get_connection()
    with conn.cursor() as cursor:
        query = "SELECT name FROM users WHERE user_id = %s AND password = %s;"
        cursor.execute(query, (user_id, password))
        result = cursor.fetchone()
    conn.close()
    return result

def insert_items_bulk(item_list, user_id="admin"):
    """엑셀에서 읽어온 튜플 리스트를 받아 DB에 대량 등록
    (이미 존재하는 NSN은 수량 합산 및 정보 업데이트 + 이력 남기기)
    """
    conn = get_connection()
    with conn.cursor() as cursor:
        query = """
            INSERT INTO item (nsn, name, price, stock) 
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
                name = VALUES(name),
                price = VALUES(price),
                stock = stock + VALUES(stock);
        """
        cursor.executemany(query, item_list)
        conn.commit()

        # 대량 등록 작업 이력 기록
        for item in item_list:
            nsn, name, price, stock = item[0], item[1], item[2], int(item[3])
            log_history(user_id, nsn, name, "엑셀등록", stock, stock)

    conn.close()

def delete_item(nsn):
    """지정한 NSN에 해당하는 물자 삭제"""
    conn = get_connection()
    with conn.cursor() as cursor:
        query = "DELETE FROM item WHERE nsn = %s;"
        cursor.execute(query, (nsn,))
        conn.commit()
    conn.close()

def search_items(nsn_keyword, name_keyword):
    """재고번호 또는 품명 키워드(LIKE 검색)로 물자 조회"""
    conn = get_connection()
    with conn.cursor() as cursor:
        query = """
            SELECT nsn, name, price, stock FROM item 
            WHERE (%s = '' OR nsn LIKE %s) 
              AND (%s = '' OR name LIKE %s);
        """
        nsn_param = f"%{nsn_keyword}%"
        name_param = f"%{name_keyword}%"
        
        cursor.execute(query, (nsn_keyword, nsn_param, name_keyword, name_param))
        result = cursor.fetchall()
    conn.close()
    return result

# 모듈 로드 시 history 테이블 자동 생성
try:
    init_history_db()
except Exception as e:
    print(f"history 테이블 생성/확인 실패: {e}")


def get_dashboard_summary():
    """대시보드 상단 요약 카드 데이터 (총 품목 수, 총 자산 가치, 부족 재고 수)"""
    conn = get_connection()
    with conn.cursor() as cursor:
        # 1. 총 품목 수, 총 자산 가치 (단가 * 수량)
        cursor.execute("SELECT COUNT(*), IFNULL(SUM(price * stock), 0) FROM item;")
        total_count, total_value = cursor.fetchone()

        # 2. 안전재고 미달 품목 수 (예: 보유 수량 10개 이하)
        cursor.execute("SELECT COUNT(*) FROM item WHERE stock <= 10;")
        low_stock_count = cursor.fetchone()[0]

    conn.close()
    return total_count, total_value, low_stock_count


def get_top_consumed_items(limit=5):
    """가장 많이 소모된 물자 Top N 조회"""
    conn = get_connection()
    with conn.cursor() as cursor:
        # action_type이 '소모처리'인 항목 중 가장 많이 소모된 물자 합산
        query = """
            SELECT item_name, ABS(SUM(qty_change)) AS total_consumed
            FROM history
            WHERE action_type = '소모처리'
            GROUP BY item_name
            ORDER BY total_consumed DESC
            LIMIT %s;
        """
        cursor.execute(query, (limit,))
        result = cursor.fetchall()
    conn.close()
    return result