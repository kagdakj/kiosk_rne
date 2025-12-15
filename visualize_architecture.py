from graphviz import Digraph
import os

path = os.path.dirname(os.path.abspath('C:\\Program Files\\Graphviz\\bin'))

def create_architecture_diagram():
    # 그래프 생성
    dot = Digraph(comment='AI Kiosk System Architecture', format='png')
    dot.attr(rankdir='LR')  # 좌우 방향 배치
    dot.attr('node', fontname='Malgun Gothic') # 한글 폰트 설정 (윈도우 기준)

    # 1. 클라이언트 영역 (라즈베리파이/키오스크)
    with dot.subgraph(name='cluster_client') as c:
        c.attr(label='Client (Raspberry Pi / Kiosk)')
        c.attr(style='filled', color='#f0f0f0')
        c.attr(fontsize='20')

        # 사용자 및 하드웨어
        c.node('User', '사용자 (User)', shape='circle', style='filled', fillcolor='white')
        c.node('Cam', '카메라 (Camera)', shape='box', style='filled', fillcolor='#e1bee7')
        c.node('Mic', '마이크 (Mic)', shape='box', style='filled', fillcolor='#e1bee7')

        # 프론트엔드 파일들
        c.node('HTML', 'index.html\n(Main UI)', shape='note', style='filled', fillcolor='#fff9c4')
        c.node('AgeJS', 'age_detection.js\n(Face API)', shape='component', style='filled', fillcolor='#bbdefb')
        c.node('VoiceJS', 'voice_recognition.js\n(Audio Recorder)', shape='component', style='filled', fillcolor='#bbdefb')

        # 내부 흐름
        c.edge('User', 'Cam', label='얼굴 노출')
        c.edge('User', 'Mic', label='음성 명령')
        c.edge('Cam', 'AgeJS', label='Video Stream')
        c.edge('Mic', 'VoiceJS', label='Audio Stream')
        c.edge('AgeJS', 'HTML', label='UI 변경 (연령별)', color='blue')
        c.edge('VoiceJS', 'HTML', label='UI 제어 (주문/장바구니)', color='blue')

    # 2. 서버/클라우드 영역
    with dot.subgraph(name='cluster_server') as s:
        s.attr(label='Server / Cloud (n8n & AI)')
        s.attr(style='filled', color='#e0f7fa')
        s.attr(fontsize='20')

        s.node('n8n', 'n8n Workflow\n(Webhook)', shape='box3d', style='filled', fillcolor='#ffccbc')
        s.node('Whisper', 'OpenAI Whisper\n(STT)', shape='ellipse', style='filled', fillcolor='white')
        s.node('LLM', 'LLM (GPT/Claude)\n(Intent Analysis)', shape='ellipse', style='filled', fillcolor='white')

        # 서버 내부 흐름
        s.edge('n8n', 'Whisper', label='Audio File')
        s.edge('Whisper', 'LLM', label='Converted Text')
        s.edge('LLM', 'n8n', label='JSON Action')

    # 3. 외부 통신 (네트워크)
    dot.edge('VoiceJS', 'n8n', label='HTTPS POST\n(Audio Blob)', style='dashed', color='red', penwidth='2.0')
    dot.edge('n8n', 'VoiceJS', label='Response\n(JSON)', style='dashed', color='green', penwidth='2.0')

    # 파일 저장
    output_path = 'project_architecture'
    dot.render(output_path, view=False)
    print(f"Diagram generated successfully: {os.path.abspath(output_path + '.png')}")

if __name__ == '__main__':
    try:
        create_architecture_diagram()
    except ImportError:
        print("오류: 'graphviz' 라이브러리가 설치되어 있지 않습니다.")
        print("pip install graphviz 명령어로 설치해주세요.")
        print("또한 Graphviz 소프트웨어가 시스템에 설치되어 있어야 합니다 (https://graphviz.org/download/).")
    except Exception as e:
        print(f"오류 발생: {e}")
