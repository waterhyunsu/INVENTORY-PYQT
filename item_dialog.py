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
            
        self.setGeometry(400, 400, 350, 350)  # 안내 레이블 공간을 위해 높이 살짝 조절

        layout = QVBoxLayout()

        # 1. 재고번호(NSN) 입력 필드
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

        # 4. 보유수량 입력 필드 (수정 모드 시 수정 불가 명시)
        stock_label_text = '보유수량(EA):'
        if self.mode == 'update':
            stock_label_text += ' (⚠️ 수량 직접 수정 불가)'
        layout.addWidget(QLabel(stock_label_text))
        
        self.input_stock = QLineEdit()
        layout.addWidget(self.input_stock)

        # 모드별 데이터 처리 및 읽기 전용 설정
        if self.mode == 'update' and self.item_data:
            self.input_nsn.setText(str(self.item_data[0]))
            # 요청사항: 수정 모드에서도 재고번호, 품명, 단가는 수정 가능하도록 허용
            self.input_name.setText(str(self.item_data[1]))
            self.input_price.setText(str(self.item_data[2]))
            
            # 보유수량은 수정 불가 처리 및 시각적 안내 (회색 배경)
            self.input_stock.setText(str(self.item_data[3]))
            self.input_stock.setReadOnly(True)
            self.input_stock.setStyleSheet("background-color: #f0f0f0; color: #666666;")

        # 저장/취소 버튼
        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton('저장')
        self.btn_save.clicked.connect(self.accept)
        
        self.btn_cancel = QPushButton('취소')
        self.btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.btn_save)

        # 수정(update) 모드일 때만 '삭제' 버튼 추가
        if self.mode == 'update':
            self.btn_delete = QPushButton('삭제')
            self.btn_delete.setStyleSheet("background-color: #ffcccc; color: red;")
            btn_layout.addWidget(self.btn_delete)

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