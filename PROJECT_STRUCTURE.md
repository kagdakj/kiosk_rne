# 프로젝트 구조도 (Architecture Diagram)

파이썬 스크립트 실행에 실패할 경우를 대비해, 마크다운으로 볼 수 있는 구조도를 제공합니다.

```mermaid
graph LR
    subgraph Client [Client (Raspberry Pi / Kiosk)]
        direction TB
        User((사용자))
        Cam[카메라]
        Mic[마이크]
        HTML[index.html<br/>(Main UI)]
        AgeJS[age_detection.js<br/>(Face API)]
        VoiceJS[voice_recognition.js<br/>(Audio Recorder)]
        
        User -->|얼굴 노출| Cam
        User -->|음성 명령| Mic
        Cam -->|Video Stream| AgeJS
        Mic -->|Audio Stream| VoiceJS
        AgeJS -->|UI 변경 (연령별)| HTML
        VoiceJS -->|UI 제어 (주문/장바구니)| HTML
    end
    
    subgraph Server [Server / Cloud]
        direction TB
        n8n[n8n Workflow<br/>(Webhook)]
        Whisper[OpenAI Whisper<br/>(STT)]
        LLM[LLM (GPT/Claude)<br/>(Intent Analysis)]
        
        n8n -->|Audio File| Whisper
        Whisper -->|Converted Text| LLM
        LLM -->|JSON Action| n8n
    end
    
    VoiceJS -.->|HTTPS POST (Audio)| n8n
    n8n -.->|Response (JSON)| VoiceJS
```

## 구조 설명

1.  **Client (Raspberry Pi)**
    *   **User**: 키오스크 사용자.
    *   **Hardware**: 카메라와 마이크를 통해 입력을 받습니다.
    *   **age_detection.js**: 카메라 영상을 분석해 연령을 추정하고 UI를 변경합니다.
    *   **voice_recognition.js**: 음성을 녹음하여 서버로 전송하고, 응답받은 액션을 수행합니다.

2.  **Server (n8n & AI)**
    *   **n8n**: 클라이언트의 요청을 받는 허브 역할을 합니다.
    *   **Whisper**: 전송받은 오디오 파일을 텍스트로 변환합니다.
    *   **LLM**: 텍스트의 의도를 분석하여 키오스크가 수행할 JSON 액션을 생성합니다.
