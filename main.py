import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTableWidget, QTableWidgetItem, 
    QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QMessageBox, QDialog, QInputDialog, QFileDialog, QMenu,
    QHeaderView, QLabel, QLineEdit
)
from PyQt5.QtCore import Qt

import db
import service
from login_dialog import LoginDialog
from item_dialog import ItemDialog

# -------------------------------------------------------------------------
class NumericTableWidgetItem(QTableWidgetItem):
    """콤마가 포함된 숫자 문자열을 올바르게 정렬하기 위한 커스텀 아이템"""
    def __lt__(self, other):
        try:
            self_val = float(self.text().replace(',', ''))
            other_val = float(other.text().replace(',', ''))
            return self_val < other_val
        except ValueError:
            return super().__lt__(other)


class SearchDialog(QDialog):
    """재고번호 또는 품명으로 검색하기 위한 입력 창"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('물자 검색')
        self.resize(300, 150)
        
        layout = QVBoxLayout()
        
        # 안내 문구
        layout.addWidget(QLabel("재고번호 또는 품명을 입력하세요"))

        # 입력 필드 레이아웃
        form_layout = QHBoxLayout()
        self.input_nsn = QLineEdit()
        self.input_nsn.setPlaceholderText("재고번호 일부/전체")
        form_layout.addWidget(QLabel("NSN:"))
        form_layout.addWidget(self.input_nsn)
        layout.addLayout(form_layout)

        name_layout = QHBoxLayout()
        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("품명 일부/전체")
        name_layout.addWidget(QLabel("품명:"))
        name_layout.addWidget(self.input_name)
        layout.addLayout(name_layout)

        # 확인/취소 버튼
        btn_layout = QHBoxLayout()
        self.btn_ok = QPushButton('검색 실행')
        self.btn_cancel = QPushButton('취소')
        
        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.btn_ok)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def get_search_filters(self):
        return self.input_nsn.text().strip(), self.input_name.text().strip()


class DelisMainWindow(QMainWindow):
    """메인 대시보드 창"""
    def __init__(self, user_id):  # 로그인한 user_id를 인자로 받음
        super().__init__()
        self.user_id = user_id
        self.initUI()
        self.load_data()

    def initUI(self):
        self.setWindowTitle('DELIS-Lite 국방 물자관리체계 (Main Dashboard)')
        self.setGeometry(300, 300, 800, 500)

        # 로그인한 계정에 따른 상태바 권한 분기 처리
        if self.user_id == '1234':
            self.statusBar().showMessage("[관리자 계정]으로 접속 중입니다.")
        else:
            self.statusBar().showMessage(f"일반 사용자 ({self.user_id}) 접속 중")

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()

        # -------------------------------------------------------------------------
        # 최상단 제어 버튼 레이아웃 (수직 2단 구조)
        # -------------------------------------------------------------------------
        ctrl_layout = QVBoxLayout()

        # [1단] 검색 및 전체 목록 버튼 (가로로 길게 한 줄 채우기)
        search_layout = QHBoxLayout()
        
        self.btn_search = QPushButton('🔍 검색')
        self.btn_search.clicked.connect(self.open_search_dialog)
        self.btn_search.setFixedHeight(35)
        
        self.btn_reset = QPushButton('🔄 전체')
        self.btn_reset.clicked.connect(self.load_data)
        self.btn_reset.setFixedHeight(35)
        
        search_layout.addWidget(self.btn_search, 9)
        search_layout.addWidget(self.btn_reset, 1)
        ctrl_layout.addLayout(search_layout)

        # [2단] 기존 4가지 제어 버튼 레이아웃 (가로 배치)
        action_layout = QHBoxLayout()

        self.btn_add = QPushButton('➕ 신규 등록')
        self.btn_add.clicked.connect(self.open_add_dialog)
        action_layout.addWidget(self.btn_add)

        # 엑셀 등록/내보내기 드롭다운 메뉴 버튼
        self.btn_excel = QPushButton('📂 등록/내보내기')
        excel_menu = QMenu(self)
        
        action_import = excel_menu.addAction('📥 엑셀 대량 등록 (Import)')
        action_export = excel_menu.addAction('📤 엑셀 내보내기 (Export)')
        
        action_import.triggered.connect(self.excel_import_action)
        action_export.triggered.connect(self.excel_export_action)
        
        self.btn_excel.setMenu(excel_menu)
        action_layout.addWidget(self.btn_excel)

        self.btn_update = QPushButton('✏️ 선택 수정 및 삭제')
        self.btn_update.clicked.connect(self.open_update_dialog)
        action_layout.addWidget(self.btn_update)

        self.btn_delete = QPushButton('🗑️ 소모 처리')
        self.btn_delete.clicked.connect(self.delete_item_action)
        action_layout.addWidget(self.btn_delete)

        ctrl_layout.addLayout(action_layout)
        # -------------------------------------------------------------------------

        main_layout.addLayout(ctrl_layout)

        # 재고 현황 표 (순번 열을 제거하고 4개 컬럼으로 설정)
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(['재고번호 (NSN)', '품명', '조달단가(원)', '보유수량'])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        
        # 정렬 기능 활성화
        self.table.setSortingEnabled(False)

        main_layout.addWidget(self.table)
        central_widget.setLayout(main_layout)

    def load_data(self):
        """db 모듈을 호출하여 목록 조회 및 컬럼별 맞춤 정렬 적용"""
        try:
            self.table.setSortingEnabled(False)
            
            result = db.get_all_items()
            self.table.setRowCount(len(result))
            
            for row_idx, row_data in enumerate(result):
                for col_idx, data in enumerate(row_data):
                    if col_idx in (2, 3) and isinstance(data, (int, float)):
                        formatted_data = f"{data:,}"
                    else:
                        formatted_data = str(data)

                    if col_idx in (2, 3):
                        item = NumericTableWidgetItem(formatted_data)
                    else:
                        item = QTableWidgetItem(formatted_data)
                        
                    # 열별로 정렬 방향 다르게 지정
                    if col_idx == 1:  # 1번 열('품명')은 '왼쪽 정렬'
                        item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                    else:             # 재고번호(0), 단가(2), 수량(3)은 '중앙 정렬'
                        item.setTextAlignment(Qt.AlignCenter)

                    self.table.setItem(row_idx, col_idx, item)

            self.table.setSortingEnabled(True)

            # 컬럼 너비 비율 조절
            header = self.table.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.ResizeToContents) # 재고번호
            header.setSectionResizeMode(1, QHeaderView.Stretch)          # 품명 (남은 공간 다 차지)
            header.setSectionResizeMode(2, QHeaderView.ResizeToContents) # 조달단가
            header.setSectionResizeMode(3, QHeaderView.ResizeToContents) # 보유수량

            total_count = len(result)
            if self.user_id == '1234':
                self.statusBar().showMessage(f"[관리자 계정]으로 접속 중입니다. | 전체 조회된 물자: {total_count}건")
            else:
                self.statusBar().showMessage(f"일반 사용자 ({self.user_id}) 접속 중 | 전체 조회된 물자: {total_count}건")

        except Exception as e:
            QMessageBox.critical(self, "DB 오류", f"데이터 조회 실패:\n{str(e)}")


    def open_search_dialog(self):
        """검색 창을 띄우고 조건에 맞는 데이터를 조회하여 테이블에 표시"""
        dialog = SearchDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            nsn_keyword, name_keyword = dialog.get_search_filters()
            
            if not nsn_keyword and not name_keyword:
                QMessageBox.warning(self, "경고", "검색어를 최소한 하나 이상 입력해주세요.")
                return

            try:
                result = db.search_items(nsn_keyword, name_keyword)
                
                self.table.setSortingEnabled(False)
                self.table.setRowCount(len(result))
                
                for row_idx, row_data in enumerate(result):
                    for col_idx, data in enumerate(row_data):
                        if col_idx in (2, 3) and isinstance(data, (int, float)):
                            formatted_data = f"{data:,}"
                        else:
                            formatted_data = str(data)

                        if col_idx in (2, 3):
                            item = NumericTableWidgetItem(formatted_data)
                        else:
                            item = QTableWidgetItem(formatted_data)
                            
                        if col_idx == 1:
                            item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                        else:
                            item.setTextAlignment(Qt.AlignCenter)

                        self.table.setItem(row_idx, col_idx, item)

                self.table.setSortingEnabled(True)

                header = self.table.horizontalHeader()
                header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
                header.setSectionResizeMode(1, QHeaderView.Stretch)
                header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
                header.setSectionResizeMode(3, QHeaderView.ResizeToContents)

                search_count = len(result)
                if self.user_id == '1234':
                    self.statusBar().showMessage(f"[관리자 계정]으로 접속 중입니다. | 검색 결과: {search_count}건")
                else:
                    self.statusBar().showMessage(f"일반 사용자 ({self.user_id}) 접속 중 | 검색 결과: {search_count}건")

            except Exception as e:
                QMessageBox.critical(self, "DB 오류", f"검색 실패:\n{str(e)}")

    def open_add_dialog(self):
        """신규 물자 등록"""
        dialog = ItemDialog(mode='add', parent=self)
        if dialog.exec_() == QDialog.Accepted:
            nsn, name, price_str, stock_str = dialog.get_data()
            if not nsn or not name or not price_str or not stock_str:
                QMessageBox.warning(self, "경고", "모든 항목을 입력해주세요.")
                return
            try:
                price, stock = int(price_str), int(stock_str)
            except ValueError:
                QMessageBox.warning(self, "경고", "단가와 수량은 숫자만 입력 가능합니다.")
                return

            try:
                db.insert_item(nsn, name, price, stock)
                QMessageBox.information(self, "성공", "신규 물자가 등록되었습니다.")
                self.load_data()
            except Exception as e:
                QMessageBox.critical(self, "DB 오류", f"등록 실패:\n{str(e)}")
                
    def excel_import_action(self):
        """엑셀 파일 선택 및 service 모듈 위임 (등록)"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "엑셀 파일 선택", "", "Excel Files (*.xlsx *.xls);;CSV Files (*.csv)"
        )
        if not file_path:
            return

        success, message = service.process_excel_import(file_path)
        
        if success:
            QMessageBox.information(self, "성공", message)
            self.load_data()
        else:
            QMessageBox.critical(self, "처리 실패", message)

    def excel_export_action(self):
        """현재 DB 데이터를 엑셀 파일로 저장하는 대화상자 호출 및 service 위임"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "엑셀 파일 저장", "inventory_export.xlsx", "Excel Files (*.xlsx);;CSV Files (*.csv)"
        )
        if not file_path:
            return

        success, message = service.export_excel(file_path)
        
        if success:
            QMessageBox.information(self, "성공", message)
        else:
            QMessageBox.critical(self, "내보내기 실패", message)

    def open_update_dialog(self):
        """물자 수정 및 삭제 처리"""
        selected_row = self.table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "선택 오류", "수정할 물자를 표에서 먼저 선택해주세요.")
            return

        nsn = self.table.item(selected_row, 0).text()
        name = self.table.item(selected_row, 1).text()
        price = self.table.item(selected_row, 2).text().replace(',', '')
        stock = self.table.item(selected_row, 3).text().replace(',', '')

        dialog = ItemDialog(mode='update', item_data=(nsn, name, price, stock), parent=self)

        def handle_dialog_delete():
            reply = QMessageBox.question(
                dialog, 
                "삭제 확인", 
                f"'{name}' ({nsn}) 물자를 완전히 삭제하시겠습니까?",
                QMessageBox.Yes | QMessageBox.No, 
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                try:
                    db.delete_item(nsn)
                    QMessageBox.information(dialog, "삭제 완료", "물자가 완전히 삭제되었습니다.")
                    dialog.accept()
                    self.load_data()
                except Exception as e:
                    QMessageBox.critical(dialog, "DB 오류", f"삭제 실패:\n{str(e)}")

        if dialog.mode == 'update':
            dialog.btn_delete.clicked.connect(handle_dialog_delete)

        if dialog.exec_() == QDialog.Accepted:
            try:
                new_name, price_str, stock_str = dialog.get_data()
            except Exception:
                return

            if not new_name or not price_str or not stock_str:
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
        current_stock = int(self.table.item(selected_row, 3).text().replace(',', ''))

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
        current_user_id = login.user_id 
        
        main_window = DelisMainWindow(current_user_id)
        main_window.show()
        sys.exit(app.exec_())
    else:
        sys.exit(0)