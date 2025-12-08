/* ===== 음성 인식 기능 ===== */
// 웹훅 URL 설정 (n8n 등)
const WEBHOOK_URL = ''; // 여기에 n8n 웹훅 URL을 입력하세요

const $voiceBtn = document.getElementById('voiceBtn');
const $voiceStatus = document.getElementById('voiceStatus');
const $voiceStatusText = document.getElementById('voiceStatusText');

// Web Speech API 지원 확인
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition = null;
let isRecording = false;

if (SpeechRecognition) {
  recognition = new SpeechRecognition();
  recognition.lang = 'ko-KR'; // 한국어 설정
  recognition.continuous = false; // 한 번의 인식 후 종료
  recognition.interimResults = true; // 중간 결과 표시

  // 음성 인식 시작 이벤트
  recognition.onstart = function() {
    console.log('음성 인식 시작');
    isRecording = true;
    $voiceBtn.classList.add('recording');
    $voiceStatus.classList.remove('hidden');
    $voiceStatusText.textContent = '🎤 듣고 있습니다... 말씀하세요';
  };

  // 음성 인식 결과 이벤트
  recognition.onresult = function(event) {
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
    if (interimTranscript) {
      $voiceStatusText.textContent = `🎤 "${interimTranscript}"`;
    }

    // 최종 결과 처리
    if (finalTranscript) {
      console.log('인식된 텍스트:', finalTranscript);
      $voiceStatusText.textContent = `✓ 인식 완료: "${finalTranscript}"`;
      
      // 웹훅으로 전송
      sendToWebhook(finalTranscript);
    }
  };

  // 음성 인식 종료 이벤트
  recognition.onend = function() {
    console.log('음성 인식 종료');
    isRecording = false;
    $voiceBtn.classList.remove('recording');
    
    // 3초 후 상태 메시지 숨기기
    setTimeout(() => {
      $voiceStatus.classList.add('hidden');
    }, 3000);
  };

  // 오류 처리
  recognition.onerror = function(event) {
    console.error('음성 인식 오류:', event.error);
    isRecording = false;
    $voiceBtn.classList.remove('recording');
    
    let errorMessage = '오류가 발생했습니다';
    switch(event.error) {
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
    
    $voiceStatusText.textContent = `❌ ${errorMessage}`;
    setTimeout(() => {
      $voiceStatus.classList.add('hidden');
    }, 3000);
  };
}

// 웹훅으로 데이터 전송
async function sendToWebhook(text) {
  if (!WEBHOOK_URL) {
    console.warn('웹훅 URL이 설정되지 않았습니다');
    $voiceStatusText.textContent = '⚠️ 웹훅 URL을 설정해주세요';
    return;
  }

  try {
    const payload = {
      text: text,
      timestamp: new Date().toISOString(),
      language: 'ko-KR'
    };

    console.log('웹훅으로 전송:', payload);
    
    const response = await fetch(WEBHOOK_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload)
    });

    if (response.ok) {
      console.log('웹훅 전송 성공');
      $voiceStatusText.textContent = `✓ 전송 완료: "${text}"`;
    } else {
      console.error('웹훅 전송 실패:', response.status);
      $voiceStatusText.textContent = `❌ 전송 실패 (${response.status})`;
    }
  } catch (error) {
    console.error('웹훅 전송 오류:', error);
    $voiceStatusText.textContent = `❌ 전송 오류: ${error.message}`;
  }
}

// 음성 인식 버튼 클릭 이벤트
if ($voiceBtn) {
  $voiceBtn.addEventListener('click', function() {
    if (!SpeechRecognition) {
      alert('이 브라우저는 음성 인식을 지원하지 않습니다.\nChrome 또는 Edge 브라우저를 사용해주세요.');
      return;
    }

    if (isRecording) {
      // 녹음 중이면 중지
      recognition.stop();
    } else {
      // 녹음 시작
      try {
        recognition.start();
      } catch (error) {
        console.error('음성 인식 시작 오류:', error);
        if (error.name === 'InvalidStateError') {
          // 이미 실행 중인 경우 무시
          console.log('음성 인식이 이미 실행 중입니다');
        }
      }
    }
  });
}
