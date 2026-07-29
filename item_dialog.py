from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton
)

class ItemDialog(QDialog):
    """신규 등록 및 수정 작업을 처리하는 독립된 서브 창 (팝업 모듈)"""
    def __init__(self, mode='add', item_data=None, parent=None):
        super().__init__(parent)
        self.mode = mode
        self.item_data = item_data
        self.initUI()

    def initUI(self):
        if self.mode == 'add':
            self.setWindowTitle('신규 군수 물자 등록')
        else:
            self.setWindowTitle('물자 제원 및 수량 수정')
            
        self.setGeometry(400, 400, 350, 320)  # 필드가 늘어나 창 높이 조절

        layout = QVBoxLayout()

        # 1. 재고번호(NSN) 입력 필드 추가
        layout.addWidget(QLabel('재고번호 (NSN):'))
        self.input_nsn = QLineEdit()
        layout.addWidget(self.input_nsn)

        # 2. 품명 입력 필드
        layout.addWidget(QLabel('품명:'))
        self.input_name = QLineEdit()
        layout.addWidget(self.input_name)

        # 3. 조달단가 입력 필드
        layout.addWidget(QLabel('조달단가(원):'))
        self.input_price = QLineEdit()
        layout.addWidget(self.input_price)

        # 4. 보유수량 입력 필드
        layout.addWidget(QLabel('보유수량(EA):'))
        self.input_stock = QLineEdit()
        layout.addWidget(self.input_stock)

        # 수정 모드일 때 데이터 자동 입력 및 NSN 수정 불가 처리
        if self.mode == 'update' and self.item_data:
            self.input_nsn.setText(str(self.item_data[0]))
            self.input_nsn.setReadOnly(True)  # 기본키(Primary Key)인 NSN은 수정 불가
            self.input_name.setText(str(self.item_data[1]))
            self.input_price.setText(str(self.item_data[2]))
            self.input_stock.setText(str(self.item_data[3]))

        # 저장/취소 버튼
        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton('저장')
        self.btn_save.clicked.connect(self.accept)
        self.btn_cancel = QPushButton('취소')
        self.btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def get_data(self):
        """입력창 값 4개를 튜플로 반환 (NSN, 품명, 단가, 수량)"""
        return (
            self.input_nsn.text().strip(),
            self.input_name.text().strip(),
            self.input_price.text().strip(),
            self.input_stock.text().strip()
        )