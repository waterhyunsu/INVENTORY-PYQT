import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QTabWidget, QVBoxLayout, QLabel
)

from login_dialog import LoginDialog
from InventoryTab import InventoryTab
from HistoryTab import HistoryTab
from DashboardTab import DashboardTab



class DelisMainWindow(QMainWindow):
    """메인 대시보드 창"""
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.initUI()

    def initUI(self):
        self.setWindowTitle('DELIS-Lite 국방 물자관리체계 (Main Dashboard)')
        self.resize(1100, 700)

        # 로그인 권한별 초기 상태바 설정
        if self.user_id == '1234':
            self.statusBar().showMessage("[관리자 계정]으로 접속 중입니다.")
        else:
            self.statusBar().showMessage(f"일반 사용자 ({self.user_id}) 접속 중")

        # 탭 위젯 구성을 통해 1~3번 탭 배치
        self.tabs = QTabWidget()

        self.tab_inventory = InventoryTab(user_id=self.user_id, parent=self)
        self.tab_history = HistoryTab(self)
        self.tab_dashboard = DashboardTab(self)

        self.tabs.addTab(self.tab_inventory, "📦 물자 관리")
        self.tabs.addTab(self.tab_history, "📋 입출고/소모 이력")
        self.tabs.addTab(self.tab_dashboard, "📊 통계 대시보드")

        self.setCentralWidget(self.tabs)


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