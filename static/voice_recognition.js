/* ===== AI 음성 제어 (Audio Recording Version for Raspberry Pi) ===== */
// 웹훅 URL 설정 (n8n에서 "Binary Data"를 받는 Webhook으로 변경 필요)
const WEBHOOK_URL = 'http://kagdakj.us.to:5678/webhook/da8e655c-86da-4261-87bb-dadbea77dc0a';

const $voiceBtn = document.getElementById('voiceBtn');
const $voiceStatus = document.getElementById('voiceStatus');
const $voiceStatusText = document.getElementById('voiceStatusText');

let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;

// 녹음 시작
async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];

        mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                audioChunks.push(event.data);
            }
        };

        mediaRecorder.onstop = () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/webm' }); // Chromium은 webm 지원
            sendAudioToWebhook(audioBlob);

            // 스트림 트랙 중지 (마이크 끄기)
            stream.getTracks().forEach(track => track.stop());
        };

        mediaRecorder.start();
        isRecording = true;

        // UI 업데이트
        $voiceBtn.classList.add('recording');
        $voiceStatus.classList.remove('hidden');
        $voiceStatusText.textContent = '🎤 듣고 있습니다... (클릭하여 종료)';

    } catch (error) {
        console.error('마이크 접근 오류:', error);
        alert('마이크 권한이 필요합니다. HTTPS 환경인지 확인하세요.\n라즈베리파이: localhost 또는 HTTPS 필수');
    }
}

// 녹음 중지
function stopRecording() {
    if (mediaRecorder && isRecording) {
        mediaRecorder.stop();
        isRecording = false;

        // UI 업데이트
        $voiceBtn.classList.remove('recording');
        $voiceStatusText.textContent = '⏳ 서버 전송 중...';
    }
}

// 웹훅으로 오디오 전송
async function sendAudioToWebhook(audioBlob) {
    if (!WEBHOOK_URL) {
        console.warn('웹훅 URL이 설정되지 않았습니다');
        return;
    }

    try {
        const formData = new FormData();
        formData.append('file', audioBlob, 'voice_command.webm');

        console.log('오디오 전송 시작:', audioBlob.size, 'bytes');
        $voiceStatusText.textContent = '⏳ AI 처리 중...';

        const response = await fetch(WEBHOOK_URL, {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            console.log('✅ 서버 응답 수신');
            try {
                const jsonResponse = await response.json();
                console.log('AI 응답:', jsonResponse);

                $voiceStatusText.textContent = '✓ 처리 완료';

                // AI 응답 처리
                handleAIResponse(jsonResponse);

                setTimeout(() => {
                    $voiceStatus.classList.add('hidden');
                }, 3000);
            } catch (e) {
                console.error('JSON 파싱 오류:', e);
                $voiceStatusText.textContent = '⚠️ 응답 형식 오류';
            }
        } else {
            throw new Error(`서버 응답 오류: ${response.status}`);
        }
    } catch (error) {
        console.error('전송 실패:', error);
        $voiceStatusText.textContent = `❌ 오류: ${error.message}`;
        setTimeout(() => $voiceStatus.classList.add('hidden'), 3000);
    }
}

// AI 응답 처리
function handleAIResponse(aiResponse) {
    const $n8nResponse = document.getElementById('n8nResponse');
    const $n8nResponseText = document.getElementById('n8nResponseText');

    // 1. 텍스트 응답 표시
    if (aiResponse.message) {
        if ($n8nResponseText && $n8nResponse) {
            $n8nResponseText.textContent = aiResponse.message;
            $n8nResponse.classList.remove('hidden');
            setTimeout(() => $n8nResponse.classList.add('hidden'), 5000);
        }
    }

    // 2. 액션 실행
    if (aiResponse.action) {
        executeAction(aiResponse.action, aiResponse.params || {});
    }
}

// 액션 실행기
function executeAction(action, params) {
    console.log('액션 실행:', action, params);
    try {
        switch (action) {
            case 'addToCart':
                handleAddToCart(params);
                break;
            case 'clearCart':
                handleClearCart();
                break;
            case 'placeOrder':
                handlePlaceOrder();
                break;
            case 'changeAge':
                handleChangeAge(params.ageGroup);
                break;
            case 'selectCategory':
                handleSelectCategory(params.category);
                break;
            case 'showMenu':
                handleShowMenu(params.menuName);
                break;
            case 'removeFromCart':
                handleRemoveFromCart(params.menuName);
                break;
            default:
                console.warn('알 수 없는 액션:', action);
        }
    } catch (e) {
        console.error('액션 실행 중 오류:', e);
    }
}

// --- 액션 핸들러들 ---

// 장바구니에 추가
function handleAddToCart(params) {
    if (!params.name) return;
    if (typeof PRODUCTS === 'undefined') return;

    const product = PRODUCTS.find(p =>
        p.name.toLowerCase().includes(params.name.toLowerCase()) ||
        params.name.toLowerCase().includes(p.name.toLowerCase())
    );

    if (product) {
        // 옵션 매핑
        const mapSize = (v) => ({ 's': 'S', 'm': 'M', 'l': 'L' }[String(v).toLowerCase()] || 'M');
        const mapSweet = (v) => ({ '0': '0', '1': '50', '2': '100' }[String(v)] || '50');
        const mapIce = (v) => ({ '0': 'less', '1': 'normal', '2': 'more' }[String(v)] || 'normal');

        const options = {
            size: mapSize(params.size),
            sweet: mapSweet(params.sweet),
            ice: mapIce(params.ice)
        };

        const qty = params.quantity || 1;

        if (typeof cart !== 'undefined') {
            for (let i = 0; i < qty; i++) {
                const key = `${product.id}-${options.size}-${options.sweet}-${options.ice}`;
                const existing = cart.find(it => `${it.id}-${it.size}-${it.sweet}-${it.ice}` === key);
                if (existing) existing.qty++;
                else cart.push({ ...product, ...options, qty: 1 });
            }
            if (typeof renderCart === 'function') renderCart();
        }
    }
}

function handleClearCart() {
    if (typeof cart !== 'undefined') {
        cart.length = 0;
        if (typeof renderCart === 'function') renderCart();
    }
}

function handlePlaceOrder() {
    if (typeof order === 'function') order();
}

function handleChangeAge(ageGroup) {
    if (typeof selectAge === 'function') selectAge(ageGroup);
}

function handleSelectCategory(category) {
    if (typeof selectCategory === 'function') selectCategory(category);
}

function handleShowMenu(menuName) {
    if (typeof PRODUCTS === 'undefined') return;
    const product = PRODUCTS.find(p => p.name.includes(menuName));
    if (product && typeof selectMenu === 'function') selectMenu(product.id);
}

function handleRemoveFromCart(menuName) {
    if (typeof cart !== 'undefined') {
        const idx = cart.findIndex(item => item.name.includes(menuName));
        if (idx !== -1) {
            cart.splice(idx, 1);
            if (typeof renderCart === 'function') renderCart();
        }
    }
}

// 버튼 이벤트 리스너
if ($voiceBtn) {
    $voiceBtn.addEventListener('click', () => {
        if (isRecording) {
            stopRecording();
        } else {
            startRecording();
        }
    });
}
