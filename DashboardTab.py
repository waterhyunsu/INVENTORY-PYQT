import platform
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, QMessageBox
)
from PyQt5.QtCore import Qt

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

import db

# 한글 폰트 깨짐 방지 설정
if platform.system() == 'Windows':
    plt.rc('font', family='Malgun Gothic')
elif platform.system() == 'Darwin':
    plt.rc('font', family='AppleGothic')
plt.rcParams['axes.unicode_minus'] = False


class DashboardTab(QWidget):
    """3번 탭: 대시보드 및 통계 차트 화면"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
        self.load_data()

    def initUI(self):
        main_layout = QVBoxLayout(self)

        # 1. 상단 컨트롤 (새로고침 버튼)
        top_layout = QHBoxLayout()
        top_layout.addStretch(1)
        self.btn_refresh = QPushButton("🔄 대시보드 새로고침")
        self.btn_refresh.setFixedHeight(35)
        self.btn_refresh.clicked.connect(self.load_data)
        top_layout.addWidget(self.btn_refresh)
        main_layout.addLayout(top_layout)

        # 2. 요약 지표 카드 레이아웃 (3개 카드를 가로 배향)
        cards_layout = QHBoxLayout()

        self.card_total_items = self.create_card("📦 관리 품목 수", "0 건", "#2B579A")
        self.card_total_value = self.create_card("💰 총 자산 가치", "0 원", "#1E7145")
        self.card_low_stock = self.create_card("⚠️ 재고 부족 물자 (10개 이하)", "0 건", "#B91D47")

        cards_layout.addWidget(self.card_total_items)
        cards_layout.addWidget(self.card_total_value)
        cards_layout.addWidget(self.card_low_stock)

        main_layout.addLayout(cards_layout)

        # 3. 하단 차트 영역 (Matplotlib Canvas)
        self.figure = Figure(figsize=(8, 4), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        main_layout.addWidget(self.canvas)

    def create_card(self, title, default_val, color_hex):
        """카드 형태의 QFrame 생성 헬퍼 함수"""
        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: #FFFFFF;
                border-left: 5px solid {color_hex};
                border-radius: 6px;
                padding: 10px;
            }}
        """)
        
        layout = QVBoxLayout(frame)
        
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("font-size: 13px; color: #666666; font-weight: bold;")
        
        lbl_val = QLabel(default_val)
        lbl_val.setStyleSheet(f"font-size: 20px; color: {color_hex}; font-weight: bold;")
        lbl_val.setAlignment(Qt.AlignRight)
        
        layout.addWidget(lbl_title)
        layout.addWidget(lbl_val)
        
        # 값을 업데이트할 수 있도록 라벨 참조를 객체에 보관
        frame.lbl_val = lbl_val
        return frame

    def load_data(self):
        """DB에서 통계 데이터를 조회하여 카드 및 차트 갱신"""
        try:
            # 1. 요약 카드 데이터 조회 및 반영
            total_count, total_value, low_stock = db.get_dashboard_summary()
            
            self.card_total_items.lbl_val.setText(f"{total_count:,} 건")
            self.card_total_value.lbl_val.setText(f"{int(total_value):,} 원")
            self.card_low_stock.lbl_val.setText(f"{low_stock:,} 건")

            # 2. Top 5 소모 물자 차트 그리기
            top_consumed = db.get_top_consumed_items(limit=5)
            self.draw_chart(top_consumed)

        except Exception as e:
            QMessageBox.critical(self, "오류", f"대시보드 데이터 로드 실패:\n{str(e)}")

    def draw_chart(self, top_data):
        """Matplotlib 막대 차트 생성"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        if not top_data:
            ax.text(0.5, 0.5, "소모 이력 데이터가 없습니다.", 
                    horizontalalignment='center', verticalalignment='center', fontsize=12)
            ax.axis('off')
        else:
            items = [row[0] for row in top_data]
            counts = [row[1] for row in top_data]

            # 막대 그래프 (Top 5 소모 수량)
            bars = ax.barh(items, counts, color='#2B579A')
            ax.invert_yaxis()  # 최상위 항목이 맨 위에 오도록 뒤집기
            ax.set_title("🔥 누적 소모량 Top 5 물자", fontsize=14, fontweight='bold', pad=15)
            ax.set_xlabel("소모 수량 (EA)", fontsize=10)

            # 수량 레이블 막대 끝에 표시
            for bar in bars:
                width = bar.get_width()
                ax.text(width + 0.3, bar.get_y() + bar.get_height()/2, f'{int(width):,} EA',
                        va='center', ha='left', fontsize=9, fontweight='bold')

            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)

        self.figure.tight_layout()
        self.canvas.draw()