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

def delete_item(nsn):
    """물자 삭제/불용 처리 (Delete)"""
    conn = get_connection()
    with conn.cursor() as cursor:
        query = "DELETE FROM item WHERE nsn = %s;"
        cursor.execute(query, (nsn,))
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