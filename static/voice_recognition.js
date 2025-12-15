/* ===== AI 음성 제어 (Realtime WebSocket Streaming) ===== */
const WS_URL = 'wss://localhost-0.tailc0f27e.ts.net:8001';
const WEBHOOK_URL = 'http://kagdakj.us.to:5678/webhook/da8e655c-86da-4261-87bb-dadbea77dc0a';

const SERVER_CHECK_INTERVAL = 5000;

const $voiceBtn = document.getElementById('voiceBtn');
const $voiceStatus = document.getElementById('voiceStatus');
const $voiceStatusText = document.getElementById('voiceStatusText');

let socket = null;
let serverAvailable = false;
let micAvailable = false;
let shouldStream = true;
let audioContext = null;
let micSource = null;
let processor = null;
let mediaStream = null;
let micInitializing = false;
let pendingSentences = [];
let realtimeText = '';
let lastSentSentence = '';

function initRealtimeVoice() {
    if (!$voiceStatus || !$voiceStatusText) return;

    showVoiceStatus('🎤 실시간 음성을 준비하는 중입니다...');
    connectToServer();
    startMicStream();

    setInterval(() => {
        if (!shouldStream) return;
        if (!socket || socket.readyState === WebSocket.CLOSED) {
            connectToServer(true);
        }
    }, SERVER_CHECK_INTERVAL);

    if ($voiceBtn) {
        $voiceBtn.title = '연결이 끊기면 클릭해서 음성 채널을 재시작하세요.';
        $voiceBtn.addEventListener('click', () => {
            restartStreaming();
        });
    }

    window.addEventListener('beforeunload', () => {
        stopStreaming(true);
    });
}

function connectToServer(force = false) {
    if (!shouldStream) return;
    if (!force && socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) {
        return;
    }

    try {
        socket = new WebSocket(WS_URL);
    } catch (err) {
        console.error('STT 서버 소켓 생성 실패:', err);
        serverAvailable = false;
        showVoiceStatus();
        return;
    }

    socket.onopen = () => {
        serverAvailable = true;
        showVoiceStatus();
    };

    socket.onclose = () => {
        serverAvailable = false;
        socket = null;
        showVoiceStatus();
    };

    socket.onerror = (err) => {
        console.error('STT 소켓 오류:', err);
    };

    socket.onmessage = handleSocketMessage;
}

async function startMicStream(force = false) {
    if (!shouldStream || micInitializing) return;
    if (!force && micAvailable && processor) return;

    micInitializing = true;

    try {
        if (!mediaStream || force) {
            mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
        }

        if (!audioContext || audioContext.state === 'closed') {
            audioContext = new AudioContext();
        } else if (audioContext.state === 'suspended') {
            await audioContext.resume();
        }

        releaseMicNodes();

        micSource = audioContext.createMediaStreamSource(mediaStream);
        processor = audioContext.createScriptProcessor(1024, 1, 1);
        processor.onaudioprocess = handleAudioProcess;
        micSource.connect(processor);
        processor.connect(audioContext.destination);

        micAvailable = true;
        showVoiceStatus();
    } catch (err) {
        micAvailable = false;
        console.error('마이크 초기화 실패:', err);
        showVoiceStatus('🎤 마이크 권한이 필요합니다. 허용 후 페이지를 새로고침하세요.');
    } finally {
        micInitializing = false;
    }
}

function handleAudioProcess(event) {
    if (!shouldStream || !socket || socket.readyState !== WebSocket.OPEN) return;
    const inputData = event.inputBuffer.getChannelData(0);
    const pcmBuffer = new Int16Array(inputData.length);

    for (let i = 0; i < inputData.length; i++) {
        let s = inputData[i] * 32768;
        s = Math.max(-32768, Math.min(32767, s));
        pcmBuffer[i] = s;
    }

    const metadata = JSON.stringify({ sampleRate: audioContext.sampleRate });
    const metadataBytes = new TextEncoder().encode(metadata);
    const metadataLength = new ArrayBuffer(4);
    new DataView(metadataLength).setUint32(0, metadataBytes.byteLength, true);

    const packet = new Blob([metadataLength, metadataBytes, pcmBuffer.buffer]);
    socket.send(packet);
}

function handleSocketMessage(event) {
    if (typeof event.data !== 'string') return;

    try {
        const data = JSON.parse(event.data);
        if (data.type === 'realtime') {
            realtimeText = data.text || '';
            showVoiceStatus();
        } else if (data.type === 'fullSentence') {
            const text = (data.text || '').trim();
            if (!text) return;
            realtimeText = '';
            enqueueSentence(text);
        }
    } catch (err) {
        console.error('STT 메시지 파싱 실패:', err);
    }
}

function enqueueSentence(text) {
    if (text === lastSentSentence) return;
    lastSentSentence = text;

    const item = { id: Date.now() + Math.random(), text };
    pendingSentences.push(item);
    showVoiceStatus();
    sendTranscriptToWebhook(item);
}

async function sendTranscriptToWebhook(sentence) {
    if (!WEBHOOK_URL) return;
    showVoiceStatus(`🛰 "${sentence.text}" 전송 중...`);

    try {
        const payload = {
            text: sentence.text,
            timestamp: new Date().toISOString(),
            language: 'ko-KR'
        };

        const response = await fetch(WEBHOOK_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            throw new Error(`웹훅 응답 오류 (${response.status})`);
        }

        const result = await response.json().catch(() => null);
        if (result) {
            handleAIResponse(result);
        }

        removeSentence(sentence.id);
        showVoiceStatus(`✓ "${sentence.text}" 처리 완료`);
        setTimeout(() => showVoiceStatus(), 1200);
    } catch (err) {
        console.error('웹훅 전송 실패:', err);
        showVoiceStatus(`❌ 웹훅 오류: ${err.message}`);
        setTimeout(() => showVoiceStatus(), 2000);
    }
}

function removeSentence(id) {
    pendingSentences = pendingSentences.filter(item => item.id !== id);
    if (!pendingSentences.length) {
        lastSentSentence = '';
    }
    showVoiceStatus();
}

async function restartStreaming() {
    showVoiceStatus('🔄 음성 채널을 재시작합니다...');
    await stopStreaming();
    shouldStream = true;
    connectToServer(true);
    startMicStream(true);
}

async function stopStreaming(fullStop = false) {
    if (socket) {
        try { socket.close(); } catch (e) { }
        socket = null;
    }
    serverAvailable = false;

    releaseMicNodes(fullStop);

    if (fullStop) {
        shouldStream = false;
        if (mediaStream) {
            mediaStream.getTracks().forEach(track => track.stop());
            mediaStream = null;
        }
        micAvailable = false;
        if (audioContext) {
            try { await audioContext.close(); } catch (e) { }
            audioContext = null;
        }
    }
}

function releaseMicNodes(stopTracks = false) {
    if (processor) {
        processor.disconnect();
        processor.onaudioprocess = null;
        processor = null;
    }
    if (micSource) {
        micSource.disconnect();
        micSource = null;
    }
    if (stopTracks && mediaStream) {
        mediaStream.getTracks().forEach(track => track.stop());
        mediaStream = null;
        micAvailable = false;
    }
}

function showVoiceStatus(message) {
    if (!$voiceStatusText || !$voiceStatus) return;
    $voiceStatus.classList.remove('hidden');

    if ($voiceBtn) {
        $voiceBtn.classList.toggle('recording', micAvailable && serverAvailable);
    }

    if (message) {
        $voiceStatusText.textContent = message;
        return;
    }

    if (!micAvailable) {
        $voiceStatusText.textContent = '🎤 마이크 권한을 허용해주세요.';
        return;
    }
    if (!serverAvailable) {
        $voiceStatusText.textContent = '🖥️ 실시간 음성 서버 연결을 대기 중입니다...';
        return;
    }

    const transcript = [...pendingSentences.map(s => s.text), realtimeText].filter(Boolean).join(' ').trim();
    $voiceStatusText.textContent = transcript || '👄 말씀해 주세요...';
}

// AI 응답 처리 이하 기존 로직 유지
function handleAIResponse(aiResponse) {
    const $n8nResponse = document.getElementById('n8nResponse');
    const $n8nResponseText = document.getElementById('n8nResponseText');

    if (aiResponse.message && $n8nResponseText && $n8nResponse) {
        $n8nResponseText.textContent = aiResponse.message;
        $n8nResponse.classList.remove('hidden');
        setTimeout(() => $n8nResponse.classList.add('hidden'), 5000);
    }

    if (aiResponse.action) {
        executeAction(aiResponse.action, aiResponse.params || {});
    }
}

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

function handleAddToCart(params) {
    if (!params || !params.name || typeof PRODUCTS === 'undefined') return;

    const product = PRODUCTS.find(p =>
        p.name.toLowerCase().includes(params.name.toLowerCase()) ||
        params.name.toLowerCase().includes(p.name.toLowerCase())
    );

    if (!product || typeof cart === 'undefined') return;

    const mapSize = (v) => ({ 's': 'S', 'm': 'M', 'l': 'L' }[String(v).toLowerCase()] || 'M');
    const mapSweet = (v) => ({ '0': '0', '1': '50', '2': '100' }[String(v)] || '50');
    const mapIce = (v) => ({ '0': 'less', '1': 'normal', '2': 'more' }[String(v)] || 'normal');

    const options = {
        size: mapSize(params.size),
        sweet: mapSweet(params.sweet),
        ice: mapIce(params.ice)
    };

    const qty = params.quantity || 1;
    for (let i = 0; i < qty; i++) {
        const key = `${product.id}-${options.size}-${options.sweet}-${options.ice}`;
        const existing = cart.find(it => `${it.id}-${it.size}-${it.sweet}-${it.ice}` === key);
        if (existing) existing.qty += 1;
        else cart.push({ ...product, ...options, qty: 1 });
    }

    if (typeof renderCart === 'function') renderCart();
}

function handleClearCart() {
    if (typeof cart === 'undefined') return;
    cart.length = 0;
    if (typeof renderCart === 'function') renderCart();
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
    if (typeof PRODUCTS === 'undefined' || typeof selectMenu !== 'function') return;
    const product = PRODUCTS.find(p => p.name.includes(menuName));
    if (product) selectMenu(product.id);
}

function handleRemoveFromCart(menuName) {
    if (typeof cart === 'undefined') return;
    const idx = cart.findIndex(item => item.name.includes(menuName));
    if (idx !== -1) {
        cart.splice(idx, 1);
        if (typeof renderCart === 'function') renderCart();
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initRealtimeVoice);
} else {
    initRealtimeVoice();
}
