import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.font_manager as fm

def create_professional_diagram():
    # 1. 그래프 및 레이아웃 설정
    G = nx.DiGraph()
    
    # 노드 정의 (Whisper 제거 및 VoiceJS 변경)
    nodes = {
        'User': {'label': 'User\n(사용자)', 'pos': (0, 1.5), 'color': '#ffffff', 'edgecolor': '#333333'},
        
        # Client Side
        'Cam': {'label': 'Camera\n(Input)', 'pos': (1, 2.2), 'color': '#e3f2fd', 'edgecolor': '#1565c0'},
        'Mic': {'label': 'Microphone\n(Input)', 'pos': (1, 0.8), 'color': '#e3f2fd', 'edgecolor': '#1565c0'},
        'AgeJS': {'label': 'Age Detection\n(face-api.js)', 'pos': (2, 2.2), 'color': '#bbdefb', 'edgecolor': '#0d47a1'},
        'VoiceJS': {'label': 'Voice Control\n(Web Speech API)', 'pos': (2, 0.8), 'color': '#bbdefb', 'edgecolor': '#0d47a1'},
        'HTML': {'label': 'Kiosk UI\n(index.html)', 'pos': (3, 1.5), 'color': '#fff9c4', 'edgecolor': '#fbc02d'},
        
        # Server Side
        'n8n': {'label': 'n8n Workflow\n(Webhook Gateway)', 'pos': (5, 1.5), 'color': '#ffccbc', 'edgecolor': '#d84315'},
        'LLM': {'label': 'LLM Agent\n(Intent Analysis)', 'pos': (6, 1.5), 'color': '#f3e5f5', 'edgecolor': '#7b1fa2'},
    }
    
    G.add_nodes_from(nodes.keys())
    pos = {k: v['pos'] for k, v in nodes.items()}
    
    # 엣지 정의 (흐름 수정: VoiceJS -> n8n -> LLM)
    edges = [
        ('User', 'Cam'), ('User', 'Mic'),
        ('Cam', 'AgeJS'), ('Mic', 'VoiceJS'),
        ('AgeJS', 'HTML'), ('VoiceJS', 'HTML'),
        ('VoiceJS', 'n8n'),
        ('n8n', 'LLM'), ('LLM', 'n8n'),
        ('n8n', 'VoiceJS')
    ]
    G.add_edges_from(edges)

    # 2. 시각화 설정
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # 배경 영역 그리기 (Client vs Server)
    # Client Region
    rect_client = patches.FancyBboxPatch((0.5, 0.2), 3.0, 2.6, boxstyle="round,pad=0.1", 
                                         linewidth=2, edgecolor='#1565c0', facecolor='#e3f2fd', alpha=0.1, zorder=0)
    ax.add_patch(rect_client)
    plt.text(2.0, 2.9, "Client Side (Browser STT)", fontsize=14, fontweight='bold', color='#0d47a1', ha='center')

    # Server Region
    rect_server = patches.FancyBboxPatch((4.5, 0.2), 2.0, 2.6, boxstyle="round,pad=0.1", 
                                         linewidth=2, edgecolor='#d84315', facecolor='#fbe9e7', alpha=0.1, zorder=0)
    ax.add_patch(rect_server)
    plt.text(5.5, 2.9, "Server Side (Cloud / n8n)", fontsize=14, fontweight='bold', color='#bf360c', ha='center')

    # 폰트 설정
    font_name = 'sans-serif'
    try:
        for font in fm.fontManager.ttflist:
            if 'Malgun Gothic' in font.name:
                font_name = 'Malgun Gothic'
                break
    except:
        pass

    # 3. 노드 그리기
    for node, attr in nodes.items():
        nx.draw_networkx_nodes(G, pos, nodelist=[node], node_color=attr['color'], 
                               node_size=4500, edgecolors=attr['edgecolor'], linewidths=2)
        
    # 4. 엣지 그리기 (Curved Arrows)
    # 일반 흐름
    nx.draw_networkx_edges(G, pos, edgelist=[e for e in edges if e not in [('VoiceJS', 'n8n'), ('n8n', 'VoiceJS')]], 
                           width=1.5, edge_color='gray', arrowsize=20, connectionstyle="arc3,rad=0.1")
    
    # 네트워크 통신 (강조)
    nx.draw_networkx_edges(G, pos, edgelist=[('VoiceJS', 'n8n')], 
                           width=2.5, edge_color='#d84315', style='dashed', arrowsize=25, connectionstyle="arc3,rad=-0.2")
    nx.draw_networkx_edges(G, pos, edgelist=[('n8n', 'VoiceJS')], 
                           width=2.5, edge_color='#2e7d32', style='dashed', arrowsize=25, connectionstyle="arc3,rad=-0.2")

    # 5. 라벨 그리기
    labels = {k: v['label'] for k, v in nodes.items()}
    nx.draw_networkx_labels(G, pos, labels, font_size=9, font_family=font_name, font_weight='bold')

    # 엣지 라벨 (데이터 흐름 설명)
    edge_labels = {
        ('User', 'Cam'): 'Visual',
        ('User', 'Mic'): 'Audio',
        ('AgeJS', 'HTML'): 'DOM Update',
        ('VoiceJS', 'n8n'): 'HTTPS POST\n(Text)',
        ('n8n', 'VoiceJS'): 'Response\n(JSON Action)',
        ('n8n', 'LLM'): 'Text Prompt'
    }
    
    # 엣지 라벨 위치 조정
    for (u, v), label in edge_labels.items():
        x1, y1 = pos[u]
        x2, y2 = pos[v]
        plt.text((x1+x2)/2, (y1+y2)/2 + 0.1, label, fontsize=8, color='#555555', 
                 ha='center', bbox=dict(facecolor='white', edgecolor='none', alpha=0.7))

    # 타이틀 및 마무리
    plt.title("AI Kiosk System Architecture (Browser STT)", fontsize=20, fontweight='bold', pad=20)
    plt.axis('off')
    plt.tight_layout()
    
    # 저장
    output_path = 'project_architecture_browser_stt.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Diagram generated successfully: {output_path}")

if __name__ == '__main__':
    try:
        create_professional_diagram()
    except Exception as e:
        print(f"오류 발생: {e}")
