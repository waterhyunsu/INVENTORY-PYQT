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

def get_all_items():
    """재고 목록 전체 조회 (Read)"""
    conn = get_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT nsn, name, price, stock FROM item;")
        result = cursor.fetchall()
    conn.close()
    return result

def insert_item(name, price, stock):
    """신규 물자 추가 (Create)"""
    conn = get_connection()
    with conn.cursor() as cursor:
        query = "INSERT INTO item (name, price, stock) VALUES (%s, %s, %s);"
        cursor.execute(query, (name, price, stock))
        conn.commit()
    conn.close()

def update_item(nsn, name, price, stock):
    """물자 정보 수정 (Update)"""
    conn = get_connection()
    with conn.cursor() as cursor:
        query = "UPDATE item SET name = %s, price = %s, stock = %s WHERE nsn = %s;"
        cursor.execute(query, (name, price, stock, nsn))
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
    return result  # 일치하는 계정이 있으면 이름 반환, 없으면 None

def insert_items_bulk(item_list):
    """엑셀에서 읽어온 튜플 리스트를 받아 한 번에 DB에 대량 등록 (NSN 포함)"""
    conn = get_connection()
    with conn.cursor() as cursor:
        # 👈 [수정] nsn을 포함하여 4개의 컬럼을 한 번에 삽입하도록 수정
        query = "INSERT INTO item (nsn, name, price, stock) VALUES (%s, %s, %s, %s);"
        cursor.executemany(query, item_list)
        conn.commit()
    conn.close()