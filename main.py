import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTableWidget, QTableWidgetItem, 
    QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QMessageBox, QDialog, QInputDialog
)

import db
from login_dialog import LoginDialog
from item_dialog import ItemDialog

class DelisMainWindow(QMainWindow):
    """메인 대시보드 창"""
    def __init__(self):
        super().__init__()
        self.initUI()
        self.load_data()

    def initUI(self):
        self.setWindowTitle('DELIS-Lite 국방 물자관리체계 (Main Dashboard)')
        self.setGeometry(300, 300, 750, 500)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()

        # 제어 버튼 레이아웃
        ctrl_layout = QHBoxLayout()

        self.btn_add = QPushButton('➕ 신규 물자 등록')
        self.btn_add.clicked.connect(self.open_add_dialog)
        ctrl_layout.addWidget(self.btn_add)

        self.btn_update = QPushButton('✏️ 선택 물자 수정')
        self.btn_update.clicked.connect(self.open_update_dialog)
        ctrl_layout.addWidget(self.btn_update)

        self.btn_delete = QPushButton('🗑️ 물자 소모 처리')
        self.btn_delete.clicked.connect(self.delete_item_action)
        ctrl_layout.addWidget(self.btn_delete)

        self.btn_load = QPushButton('🔄 현황 새로고침')
        self.btn_load.clicked.connect(self.load_data)
        ctrl_layout.addWidget(self.btn_load)

        main_layout.addLayout(ctrl_layout)

        # 재고 현황 표
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(['재고번호 (NSN)', '품명', '조달단가', '보유수량'])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        main_layout.addWidget(self.table)

        central_widget.setLayout(main_layout)

    def load_data(self):
        """db 모듈을 호출하여 목록 조회"""
        try:
            result = db.get_all_items()
            self.table.setRowCount(len(result))
            for row_idx, row_data in enumerate(result):
                for col_idx, data in enumerate(row_data):
                    item = QTableWidgetItem(str(data))
                    self.table.setItem(row_idx, col_idx, item)
        except Exception as e:
            QMessageBox.critical(self, "DB 오류", f"데이터 조회 실패:\n{str(e)}")

    def open_add_dialog(self):
        """신규 물자 등록"""
        dialog = ItemDialog(mode='add', parent=self)
        if dialog.exec_() == QDialog.Accepted:
            name, price_str, stock_str = dialog.get_data()
            if not name or not price_str or not stock_str:
                QMessageBox.warning(self, "경고", "모든 항목을 입력해주세요.")
                return
            try:
                price, stock = int(price_str), int(stock_str)
            except ValueError:
                QMessageBox.warning(self, "경고", "단가와 수량은 숫자만 입력 가능합니다.")
                return

            try:
                db.insert_item(name, price, stock)
                QMessageBox.information(self, "성공", "신규 물자가 등록되었습니다.")
                self.load_data()
            except Exception as e:
                QMessageBox.critical(self, "DB 오류", f"등록 실패:\n{str(e)}")

    def open_update_dialog(self):
        """물자 수정"""
        selected_row = self.table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "선택 오류", "수정할 물자를 표에서 먼저 선택해주세요.")
            return

        nsn = self.table.item(selected_row, 0).text()
        name = self.table.item(selected_row, 1).text()
        price = self.table.item(selected_row, 2).text()
        stock = self.table.item(selected_row, 3).text()

        dialog = ItemDialog(mode='update', item_data=(nsn, name, price, stock), parent=self)
        if dialog.exec_() == QDialog.Accepted:
            new_name, price_str, stock_str = dialog.get_data()
            if not new_name or not price_str or not stock_str:
                QMessageBox.warning(self, "경고", "모든 항목을 입력해주세요.")
                return
            try:
                new_price, new_stock = int(price_str), int(stock_str)
            except ValueError:
                QMessageBox.warning(self, "경고", "단가와 수량은 숫자만 입력 가능합니다.")
                return

            try:
                db.update_item(nsn, new_name, new_price, new_stock)
                QMessageBox.information(self, "성공", "물자 정보가 수정되었습니다.")
                self.load_data()
            except Exception as e:
                QMessageBox.critical(self, "DB 오류", f"수정 실패:\n{str(e)}")

    def delete_item_action(self):
        """선택한 물자의 특정 수량 소모 처리"""
        selected_row = self.table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "선택 오류", "소모 처리할 물자를 표에서 먼저 선택해주세요.")
            return

        nsn = self.table.item(selected_row, 0).text()
        name = self.table.item(selected_row, 1).text()
        current_stock = int(self.table.item(selected_row, 3).text())

        if current_stock <= 0:
            QMessageBox.warning(self, "소모 불가", f"'{name}' 물자의 보유 수량이 0입니다.")
            return

        qty, ok = QInputDialog.getInt(
            self, 
            "물자 소모 처리", 
            f"'{name}' (현재고: {current_stock} EA)\n소모할 수량을 입력하세요:", 
            1, 1, current_stock, 1
        )

        if ok:
            try:
                db.consume_stock(nsn, qty)
                QMessageBox.information(self, "처리 완료", f"'{name}' {qty} EA가 소모 처리되었습니다.")
                self.load_data()
            except Exception as e:
                QMessageBox.critical(self, "DB 오류", str(e))


if __name__ == '__main__':
    app = QApplication(sys.argv)

    login = LoginDialog()
    if login.exec_() == LoginDialog.Accepted:
        main_window = DelisMainWindow()
        main_window.show()
        sys.exit(app.exec_())
    else:
        sys.exit(0)