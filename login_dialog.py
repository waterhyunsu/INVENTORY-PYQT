from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
)

class LoginDialog(QDialog):
    """사용자 로그인 창"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        self.setWindowTitle('DELIS-Lite 사용자 인증')
        self.setGeometry(400, 400, 300, 180)

        layout = QVBoxLayout()

        # 아이디 입력
        layout.addWidget(QLabel('군번 / 아이디:'))
        self.input_id = QLineEdit()
        layout.addWidget(self.input_id)

        # 비밀번호 입력
        layout.addWidget(QLabel('비밀번호:'))
        self.input_pw = QLineEdit()
        self.input_pw.setEchoMode(QLineEdit.Password)  # 입력 글자 숨김 처리
        layout.addWidget(self.input_pw)

        # 로그인 버튼
        self.btn_login = QPushButton('로그인')
        self.btn_login.clicked.connect(self.try_login)
        layout.addWidget(self.btn_login)

        self.setLayout(layout)
        self.user_name = None

    def try_login(self):
        user_id = self.input_id.text().strip()
        password = self.input_pw.text().strip()

        if not user_id or not password:
            QMessageBox.warning(self, "경고", "아이디와 비밀번호를 모두 입력해주세요.")
            return

        import db
        user = db.check_login(user_id, password)
        if user:
            self.user_name = user[0]
            self.user_id = user_id  # 로그인 성공한 아이디를 객체 변수에 저장, 이후 메인 모듈에서 관리자계정 식별 
            self.accept()  
        else:
            QMessageBox.critical(self, "로그인 실패", "아이디 또는 비밀번호가 올바르지 않습니다.")