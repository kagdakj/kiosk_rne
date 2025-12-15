# 🧠 n8n 음성 제어 워크플로우 설정 가이드

라즈베리파이에서 보낸 "오디오 파일"을 받아 텍스트로 변환(STT)하고, AI가 분석하여 JSON 액션을 반환하는 워크플로우입니다.

---

## 1. 노드 구성 요약
워크플로우는 다음 4개의 노드로 연결됩니다.

`Webhook` ➔ `OpenAI (Whisper)` ➔ `OpenAI (Chat Model)` ➔ `Respond to Webhook`

---

## 2. 단계별 상세 설정

### ① Webhook Node (시작점)
키오스크에서 보낸 오디오 파일을 받습니다.
- **HTTP Method**: `POST`
- **Path**: `webhook/rne` (자바스크립트의 URL과 일치해야 함)
- **Authentication**: `None`
- **Response Mode**: `When Last Node Finishes` (마지막에 응답)
- **Binary Data**: ✅ On (켜기)
- **Binary Property**: `file` (중요: JS에서 `formData.append('file', ...)`로 보낸 이름)

### ② OpenAI Node (Whisper - STT)
받은 오디오를 텍스트로 변환합니다.
- **Resource**: `Audio`
- **Operation**: `Transcribe`
- **Binary Data Input**: ✅ On
- **Input Binary Field**: `file`

### ③ OpenAI Node (Chat Model - LLM)
변환된 텍스트를 분석해서 JSON 명령을 만듭니다.
- **Resource**: `Chat`
- **Model**: `gpt-4o` 또는 `gpt-3.5-turbo`
- **System Message**: 아래 **[AI 프롬프트]** 내용을 복사해서 붙여넣으세요.
- **User Message**: `Expression`을 선택하고 이전 노드(Whisper)의 `text` 결과를 연결합니다.
- **Response Format**: `JSON` (Must return valid JSON)

### ④ Respond to Webhook Node (응답)
최종 JSON을 키오스크로 돌려줍니다.
- **Respond With**: `JSON`
- **Response Body**: 이전 노드(LLM)의 Output JSON을 그대로 전달합니다.

---

## 3. [AI 프롬프트] (System Prompt)

LLM 노드의 **System Message**에 아래 내용을 그대로 넣어주세요.

```markdown
당신은 스마트 키오스크의 AI 주문 도우미입니다.
사용자의 음성 입력을 분석하여 다음 JSON 형식으로 응답해야 합니다.

가능한 액션(action):
1. "addToCart": 메뉴 주문 (name, quantity, size, sweet, ice)
2. "removeFromCart": 장바구니에서 삭제 (menuName)
3. "placeOrder": 주문 완료 및 결제 진행
4. "clearCart": 장바구니 비우기
5. "changeAge": 연령 모드 변경 (ageGroup: 'child', 'teen', 'adult', 'senior')
6. "selectCategory": 카테고리 이동 (category: '커피', '티', '디저트')

메뉴 데이터:
- 커피: 아메리카노, 카페라떼, 카푸치노, 바닐라라떼
- 티: 아이스티, 캐모마일, 페퍼민트
- 디저트: 치즈케이크, 쿠키, 마카롱

응답 규칙:
1. 오직 JSON 형식만 반환할 것. (Markdown 코드 블록 없이 순수 JSON)
2. 사용자의 의도가 불분명하면 message 필드에 질문을 포함할 것.
3. 옵션이 언급되지 않으면 기본값(size: 'm', sweet: 1, ice: 1)을 사용할 것.

예시 1:
사용자: "아이스 아메리카노 한 잔이랑 쿠키 하나 줘"
응답:
{
  "message": "아이스 아메리카노와 쿠키를 담았습니다.",
  "action": "addToCart",
  "params": {
    "name": "아메리카노",
    "quantity": 1,
    "ice": 2,
    "items": [
        {"name": "아메리카노", "quantity": 1, "ice": 2},
        {"name": "쿠키", "quantity": 1}
    ]
  }
}

예시 2:
사용자: "결제해줘"
응답:
{
  "message": "주문을 완료합니다.",
  "action": "placeOrder"
}
```

---

## 4. 문제 해결 (Troubleshooting)

- **오류: "No binary data exists"**
  - Webhook 노드에서 `Binary Data` 옵션이 켜져 있는지 확인하세요.
  - JS 코드에서 `formData.append('file', ...)`로 보낸 이름 `file`이 Webhook 설정과 일치하는지 확인하세요.

- **오류: "JSON 파싱 실패"**
  - LLM이 순수 JSON이 아닌 Markdown(```json ... ```)을 포함해서 응답했을 수 있습니다. 프롬프트에 "Markdown 없이 순수 JSON만 반환하라"는 지시를 강조하세요.
