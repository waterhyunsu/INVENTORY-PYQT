import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTableWidget, QTableWidgetItem, 
    QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QMessageBox, QDialog, QInputDialog, QFileDialog, QMenu
)
from PyQt5.QtCore import Qt

import db
import service
from login_dialog import LoginDialog
from item_dialog import ItemDialog

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

        # 제어 버튼 레이아웃
        ctrl_layout = QHBoxLayout()

        self.btn_add = QPushButton('➕ 신규 등록')
        self.btn_add.clicked.connect(self.open_add_dialog)
        ctrl_layout.addWidget(self.btn_add)

        # 엑셀 등록/내보내기 드롭다운 메뉴 버튼
        self.btn_excel = QPushButton('📂 등록/내보내기')
        excel_menu = QMenu(self)
        
        action_import = excel_menu.addAction('📥 엑셀 대량 등록 (Import)')
        action_export = excel_menu.addAction('📤 엑셀 내보내기 (Export)')
        
        action_import.triggered.connect(self.excel_import_action)
        action_export.triggered.connect(self.excel_export_action)
        
        self.btn_excel.setMenu(excel_menu)
        ctrl_layout.addWidget(self.btn_excel)

        self.btn_update = QPushButton('✏️ 선택 수정')
        self.btn_update.clicked.connect(self.open_update_dialog)
        ctrl_layout.addWidget(self.btn_update)

        self.btn_delete = QPushButton('🗑️ 소모 처리')
        self.btn_delete.clicked.connect(self.delete_item_action)
        ctrl_layout.addWidget(self.btn_delete)

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
        """db 모듈을 호출하여 목록 조회 및 콤마/중앙정렬 적용"""
        try:
            self.table.setSortingEnabled(False)
            
            result = db.get_all_items()
            self.table.setRowCount(len(result))
            
            for row_idx, row_data in enumerate(result):
                for col_idx, data in enumerate(row_data):
                    # 조달단가(col_idx 2) 및 보유수량(col_idx 3) 콤마 처리
                    if col_idx in (2, 3) and isinstance(data, (int, float)):
                        formatted_data = f"{data:,}"
                    else:
                        formatted_data = str(data)

                    # 🌟 숫자 컬럼(2, 3번)은 정렬용 커스텀 아이템 적용, 그 외는 기본 아이템 적용
                    if col_idx in (2, 3):
                        item = NumericTableWidgetItem(formatted_data)
                    else:
                        item = QTableWidgetItem(formatted_data)
                        
                    item.setTextAlignment(Qt.AlignCenter)  # 모든 셀 중앙 정렬
                    self.table.setItem(row_idx, col_idx, item)

            self.table.setSortingEnabled(True)

        except Exception as e:
            QMessageBox.critical(self, "DB 오류", f"데이터 조회 실패:\n{str(e)}")

    def open_add_dialog(self):
        """신규 물자 등록"""
        dialog = ItemDialog(mode='add', parent=self)
        if dialog.exec_() == QDialog.Accepted:
            nsn, name, price_str, stock_str = dialog.get_data()  # 👈 4개로 받기
            if not nsn or not name or not price_str or not stock_str:
                QMessageBox.warning(self, "경고", "모든 항목을 입력해주세요.")
                return
            try:
                price, stock = int(price_str), int(stock_str)
            except ValueError:
                QMessageBox.warning(self, "경고", "단가와 수량은 숫자만 입력 가능합니다.")
                return

            try:
                db.insert_item(nsn, name, price, stock)  # 👈 db에 nsn도 함께 전달
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

        # 💡 [추가] 다이얼로그 내부에 생성된 '삭제' 버튼 클릭 시 실행될 내부 함수
        def handle_dialog_delete():
            # 1차 확인창 (정말 삭제할 것인지 묻기)
            reply = QMessageBox.question(
                dialog, 
                "삭제 확인", 
                f"'{name}' ({nsn}) 물자를 완전히 삭제하시겠습니까?",
                QMessageBox.Yes | QMessageBox.No, 
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                try:
                    # db 모듈의 삭제 함수 호출 (※ db.py에 delete_item 함수가 있어야 합니다)
                    db.delete_item(nsn)
                    QMessageBox.information(dialog, "삭제 완료", "물자가 완전히 삭제되었습니다.")
                    dialog.accept()  # 다이얼로그 창 닫기
                    self.load_data() # 메인 화면 목록 새로고침
                except Exception as e:
                    QMessageBox.critical(dialog, "DB 오류", f"삭제 실패:\n{str(e)}")

        # update 모드일 때만 삭제 버튼 시그널 연결
        if dialog.mode == 'update':
            dialog.btn_delete.clicked.connect(handle_dialog_delete)

        # 다이얼로그 실행 및 일반 수정(저장) 처리
        if dialog.exec_() == QDialog.Accepted:
            # 삭제 버튼을 눌러서 이미 창이 닫힌 경우(accept된 경우) 수정 로직을 타지 않도록 방어 코드 추가
            # (삭제 시 dialog.accept()를 호출했으므로, DB에 해당 nsn이 여전히 존재하는지 체크하거나 분기할 수 있습니다)
            try:
                # 만약 방금 삭제된 상태가 아니라면 일반 수정 로직 진행
                # (삭제 후에는 다이얼로그가 닫히므로 get_data() 호출 시 예외가 안 나도록 간단히 체크)
                new_name, price_str, stock_str = dialog.get_data()
            except Exception:
                return  # 삭제로 인해 다이얼로그가 닫힌 경우 무시

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

#  숫자 데이터에 , 적용하려고 문자열 형식으로 변환하니 오름차순 내림차순 시 비정상 작동하는걸 교정하기 위함
class NumericTableWidgetItem(QTableWidgetItem):
    """콤마가 포함된 숫자 문자열을 올바르게 정렬하기 위한 커스텀 아이템"""
    def __lt__(self, other):
        try:
            # 콤마 제거 후 숫자로 변환하여 대소 비교
            self_val = float(self.text().replace(',', ''))
            other_val = float(other.text().replace(',', ''))
            return self_val < other_val
        except ValueError:
            # 숫자로 변환할 수 없는 경우 기본 문자열 비교 수행
            return super().__lt__(other)


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