import matplotlib.pyplot as plt
from matplotlib import font_manager, rc

# 한글 폰트 설정 (Windows: Malgun Gothic, macOS: AppleGothic, Linux: NanumGothic)
plt.rcParams['font.family'] = 'Malgun Gothic'  # 윈도우용
# plt.rcParams['font.family'] = 'AppleGothic'  # 맥용
# plt.rcParams['font.family'] = 'NanumGothic'  # 리눅스용
plt.rcParams['axes.unicode_minus'] = False  # 마이너스 깨짐 방지

# 데이터
labels = ["15.5 / I1", "11.16 / I2", "8.3 / I3"]
percentages = [100, 52.8, 30.6]

# 그래프 그리기
plt.figure(figsize=(6, 4))
bars = plt.bar(labels, percentages, color=['orange', 'gold', 'skyblue'])
plt.title("비율 백분율 그래프 (분자 / Ii)")
plt.ylabel("비율 (%)")
plt.ylim(0, 110)
plt.grid(axis='y', linestyle='--', alpha=0.7)

# 막대 위에 값 표시
for bar, val in zip(bars, percentages):
    plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 2, f"{val:.1f}%",
             ha='center', va='bottom', fontsize=10)

plt.show()
