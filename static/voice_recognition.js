/* ===== AI 음성 제어 키오스크 (Web Speech API) ===== */

// 웹훅 URL 설정
const WEBHOOK_URL = 'https://n8n.risegbsh.dpdns.org/webhook/rne';

// DOM 요소 참조
const $voiceBtn = document.getElementById('voiceBtn');
const $voiceStatus = document.getElementById('voiceStatus');
const $voiceStatusText = document.getElementById('voiceStatusText');
const $n8nResponse = document.getElementById('n8nResponse');
const $n8nResponseText = document.getElementById('n8nResponseText');

// Web Speech API
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition = null;
let isRecording = false;

// 음성 인식 초기화
if (SpeechRecognition) {
    recognition = new SpeechRecognition();
    recognition.lang = 'ko-KR';
    recognition.continuous = false;
    recognition.interimResults = true;

    recognition.onstart = function () {
        console.log('🎤 음성 인식 시작');
        isRecording = true;
        if ($voiceBtn) $voiceBtn.classList.add('recording');
        if ($voiceStatus) $voiceStatus.classList.remove('hidden');
        if ($voiceStatusText) $voiceStatusText.textContent = '🎤 듣고 있습니다... 말씀하세요';
    };

    recognition.onresult = function (event) {
        let interimTranscript = '';
        let finalTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; i++) {
            const transcript = event.results[i][0].transcript;
            if (event.results[i].isFinal) {
                finalTranscript += transcript;
            } else {
                interimTranscript += transcript;
            }
        }

        // 중간 결과 표시
        if (interimTranscript && $voiceStatusText) {
            $voiceStatusText.textContent = `🎤 "${interimTranscript}"`;
        }

        // 최종 결과 처리
        if (finalTranscript) {
            console.log('✅ 인식된 텍스트:', finalTranscript);
            if ($voiceStatusText) $voiceStatusText.textContent = `✓ 인식 완료: "${finalTranscript}"`;
            sendToAI(finalTranscript);
        }
    };

    recognition.onend = function () {
        console.log('🛑 음성 인식 종료');
        isRecording = false;
        if ($voiceBtn) $voiceBtn.classList.remove('recording');
        if ($voiceStatus) {
            setTimeout(() => {
                $voiceStatus.classList.add('hidden');
            }, 3000);
        }
    };

    recognition.onerror = function (event) {
        console.error('❌ 음성 인식 오류:', event.error);
        isRecording = false;
        if ($voiceBtn) $voiceBtn.classList.remove('recording');

        let errorMessage = '오류가 발생했습니다';
        switch (event.error) {
            case 'no-speech':
                errorMessage = '음성이 감지되지 않았습니다';
                break;
            case 'audio-capture':
                errorMessage = '마이크를 찾을 수 없습니다';
                break;
            case 'not-allowed':
                errorMessage = '마이크 권한이 거부되었습니다';
                break;
            case 'network':
                errorMessage = '네트워크 오류가 발생했습니다';
                break;
        }

        if ($voiceStatusText) {
            $voiceStatusText.textContent = `❌ ${errorMessage}`;
            if ($voiceStatus) {
                setTimeout(() => {
                    $voiceStatus.classList.add('hidden');
                }, 3000);
            }
        }
    };
}

// ===== AI에게 음성 텍스트 전송 =====
async function sendToAI(text) {
    if (!WEBHOOK_URL) {
        console.warn('⚠️ 웹훅 URL이 설정되지 않았습니다');
        if ($voiceStatusText) $voiceStatusText.textContent = '⚠️ 웹훅 URL을 설정해주세요';
        return;
    }

    try {
        const payload = {
            text: text,
            timestamp: new Date().toISOString(),
            language: 'ko-KR'
        };

        console.log('📤 AI에게 전송:', payload);

        const response = await fetch(WEBHOOK_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload)
        });

        if (response.ok) {
            console.log('✅ AI 응답 수신');
            if ($voiceStatusText) $voiceStatusText.textContent = `✓ 전송 완료: "${text}"`;

            try {
                const aiResponse = await response.json();
                console.log('🤖 AI 응답:', aiResponse);

                // 메시지 표시
                if (aiResponse.message && $n8nResponseText && $n8nResponse) {
                    $n8nResponseText.textContent = aiResponse.message;
                    $n8nResponse.classList.remove('hidden');

                    setTimeout(() => {
                        $n8nResponse.classList.add('hidden');
                    }, 5000);
                }

                // AI가 지시한 액션 실행
                if (aiResponse.action) {
                    executeAction(aiResponse.action, aiResponse.params || {});
                }

            } catch (error) {
                console.error('❌ AI 응답 처리 오류:', error);
            }
        } else {
            console.error('❌ AI 전송 실패:', response.status);
            if ($voiceStatusText) $voiceStatusText.textContent = `❌ 전송 실패 (${response.status})`;
        }
    } catch (error) {
        console.error('❌ 네트워크 오류:', error);
        if ($voiceStatusText) $voiceStatusText.textContent = `❌ 전송 오류: ${error.message}`;
    }
}

// ===== AI 액션 실행 =====
function executeAction(action, params) {
    console.log('🎯 액션 실행:', action, params);

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
            console.warn('⚠️ 알 수 없는 액션:', action);
    }
}

// ===== 액션 핸들러 =====

function handleAddToCart(params) {
    if (!params || !params.name) {
        console.error('❌ 메뉴 이름이 없습니다');
        return;
    }

    if (typeof PRODUCTS === 'undefined') {
        console.error('❌ PRODUCTS 배열을 찾을 수 없습니다');
        return;
    }

    const product = PRODUCTS.find(p =>
        p.name.toLowerCase().includes(params.name.toLowerCase()) ||
        params.name.toLowerCase().includes(p.name.toLowerCase())
    );

    if (!product) {
        console.warn(`⚠️ 메뉴를 찾을 수 없습니다: ${params.name}`);
        return;
    }

    // 옵션 매핑
    const mapSize = (value) => {
        const map = { 's': 'S', 'm': 'M', 'l': 'L' };
        return map[String(value).toLowerCase()] || 'M';
    };

    const mapSweet = (value) => {
        const map = { '0': '0', '1': '50', '2': '100' };
        return map[String(value)] || '50';
    };

    const mapIce = (value) => {
        const map = { '0': 'less', '1': 'normal', '2': 'more' };
        return map[String(value)] || 'normal';
    };

    const options = {
        size: mapSize(params.size || 'm'),
        sweet: mapSweet(params.sweet !== undefined ? params.sweet : 1),
        ice: mapIce(params.ice !== undefined ? params.ice : 1)
    };

    const quantity = params.quantity || 1;

    console.log(`✅ 추가: ${product.name} x${quantity}`, options);

    if (typeof cart === 'undefined') {
        console.error('❌ cart 배열을 찾을 수 없습니다');
        return;
    }

    for (let i = 0; i < quantity; i++) {
        const key = `${product.id}-${options.size}-${options.sweet}-${options.ice}`;
        const existing = cart.find(item =>
            `${item.id}-${item.size}-${item.sweet}-${item.ice}` === key
        );

        if (existing) {
            existing.qty += 1;
        } else {
            cart.push({
                ...product,
                ...options,
                qty: 1
            });
        }
    }

    if (typeof renderCart === 'function') {
        renderCart();
        console.log('✅ 장바구니 업데이트 완료');
    }
}

function handleClearCart() {
    if (typeof cart === 'undefined') {
        console.error('❌ cart 배열을 찾을 수 없습니다');
        return;
    }

    cart.length = 0;

    if (typeof renderCart === 'function') {
        renderCart();
        console.log('✅ 장바구니 비움');
    }
}

function handlePlaceOrder() {
    if (typeof order === 'function') {
        order();
        console.log('✅ 주문 실행');
    } else {
        console.error('❌ order 함수를 찾을 수 없습니다');
    }
}

function handleChangeAge(ageGroup) {
    const validAges = ['child', 'teen', 'adult', 'senior'];
    if (!validAges.includes(ageGroup)) {
        console.warn('⚠️ 잘못된 연령대:', ageGroup);
        return;
    }

    if (typeof selectAge === 'function') {
        selectAge(ageGroup);
        console.log('✅ 연령 변경:', ageGroup);
    } else {
        console.error('❌ selectAge 함수를 찾을 수 없습니다');
    }
}

function handleSelectCategory(category) {
    const validCategories = ['커피', '티', '디저트'];
    if (!validCategories.includes(category)) {
        console.warn('⚠️ 잘못된 카테고리:', category);
        return;
    }

    if (typeof selectCategory === 'function') {
        selectCategory(category);
        console.log('✅ 카테고리 선택:', category);
    } else {
        console.error('❌ selectCategory 함수를 찾을 수 없습니다');
    }
}

function handleShowMenu(menuName) {
    if (typeof PRODUCTS === 'undefined') {
        console.error('❌ PRODUCTS 배열을 찾을 수 없습니다');
        return;
    }

    const product = PRODUCTS.find(p =>
        p.name.toLowerCase().includes(menuName.toLowerCase())
    );

    if (!product) {
        console.warn(`⚠️ 메뉴를 찾을 수 없습니다: ${menuName}`);
        return;
    }

    if (typeof selectMenu === 'function') {
        selectMenu(product.id);
        console.log('✅ 메뉴 상세 보기:', product.name);
    } else {
        console.error('❌ selectMenu 함수를 찾을 수 없습니다');
    }
}

function handleRemoveFromCart(menuName) {
    if (typeof cart === 'undefined') {
        console.error('❌ cart 배열을 찾을 수 없습니다');
        return;
    }

    const index = cart.findIndex(item =>
        item.name.toLowerCase().includes(menuName.toLowerCase())
    );

    if (index !== -1) {
        cart.splice(index, 1);
        if (typeof renderCart === 'function') {
            renderCart();
            console.log('✅ 장바구니에서 제거:', menuName);
        }
    } else {
        console.warn(`⚠️ 장바구니에서 찾을 수 없습니다: ${menuName}`);
    }
}

// ===== 음성 인식 버튼 이벤트 =====
if ($voiceBtn) {
    $voiceBtn.addEventListener('click', function () {
        if (!SpeechRecognition) {
            alert('이 브라우저는 음성 인식을 지원하지 않습니다.\nChrome 또는 Edge 브라우저를 사용해주세요.');
            return;
        }

        if (!recognition) {
            console.error('❌ 음성 인식 초기화 실패');
            return;
        }

        if (isRecording) {
            recognition.stop();
        } else {
            try {
                recognition.start();
            } catch (error) {
                console.error('❌ 음성 인식 시작 오류:', error);
                if (error.name === 'InvalidStateError') {
                    console.log('⚠️ 음성 인식이 이미 실행 중입니다');
                }
            }
        }
    });
}
