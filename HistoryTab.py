# HistoryTab.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QMessageBox, QHeaderView, QLabel, QLineEdit, QComboBox
)
from PyQt5.QtCore import Qt
import db

class HistoryTab(QWidget):
    """2번 탭: 입출고 및 소모 이력 관리 화면"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
        self.load_data()

    def initUI(self):
        main_layout = QVBoxLayout(self)

        # 상단 필터/검색 레이아웃
        filter_layout = QHBoxLayout()

        filter_layout.addWidget(QLabel("작업 구분:"))
        self.combo_action = QComboBox()
        self.combo_action.addItems(["전체", "신규등록", "수량수정", "소모처리", "엑셀등록", "완전삭제"])
        self.combo_action.currentTextChanged.connect(self.filter_data)
        filter_layout.addWidget(self.combo_action)

        filter_layout.addWidget(QLabel("검색어:"))
        self.input_search = QLineEdit()
        self.input_search.setPlaceholderText("재고번호, 품명, 작업자")
        self.input_search.textChanged.connect(self.filter_data)
        filter_layout.addWidget(self.input_search)

        self.btn_refresh = QPushButton("🔄 새로고침")
        self.btn_refresh.clicked.connect(self.load_data)
        filter_layout.addWidget(self.btn_refresh)

        main_layout.addLayout(filter_layout)

        # 이력 표
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            '일시', '작업자', '재고번호 (NSN)', '품명', '작업구분', '변동수량', '최종재고'
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        main_layout.addWidget(self.table)

        self.raw_data = [] # 원본 데이터 보관용

    def load_data(self):
        """DB에서 전체 이력 조회"""
        try:
            self.raw_data = db.get_all_history()
            self.filter_data()
        except Exception as e:
            QMessageBox.critical(self, "DB 오류", f"이력 조회 실패:\n{str(e)}")

    def filter_data(self):
        """선택된 구분 및 검색어로 표 필터링"""
        action_filter = self.combo_action.currentText()
        search_kw = self.input_search.text().strip().lower()

        filtered = []
        for row in self.raw_data:
            # row: (timestamp, user_id, nsn, item_name, action_type, qty_change, current_stock)
            time_str, user_id, nsn, name, action, qty, stock = row

            # 1. 작업 구분 필터링
            if action_filter != "전체" and action != action_filter:
                continue

            # 2. 키워드 검색 필터링 (재고번호, 품명, 작업자)
            if search_kw:
                match = (search_kw in str(nsn).lower() or 
                         search_kw in str(name).lower() or 
                         search_kw in str(user_id).lower())
                if not match:
                    continue

            filtered.append(row)

        self.display_table(filtered)

    def display_table(self, data):
        """표에 데이터 출력"""
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(data))

        for row_idx, row_data in enumerate(data):
            for col_idx, value in enumerate(row_data):
                # 변동수량 및 최종재고 천단위 콤마 포맷팅
                if col_idx in (5, 6) and isinstance(value, (int, float)):
                    # 변동수량에 + 기호 추가
                    if col_idx == 5 and value > 0:
                        formatted_value = f"+{value:,}"
                    else:
                        formatted_value = f"{value:,}"
                else:
                    formatted_value = str(value) if value is not None else ""

                item = QTableWidgetItem(formatted_value)
                
                # 정렬 설정
                if col_idx in (0, 1, 2, 4):  # 일시, 작업자, NSN, 구분 -> 중앙 정렬
                    item.setTextAlignment(Qt.AlignCenter)
                elif col_idx == 3:          # 품명 -> 왼쪽 정렬
                    item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                else:                       # 수량들 -> 오른쪽 정렬
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

                self.table.setItem(row_idx, col_idx, item)

        self.table.setSortingEnabled(True)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)