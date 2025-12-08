/* ===== 카메라 자동 연령 감지 기능 ===== */

// face-api.js CDN이 로드되었는지 확인
const faceapiAvailable = typeof faceapi !== 'undefined';

const MODEL_URLS = [
    './static/models',
    'https://cdn.jsdelivr.net/gh/justadudewhohacks/face-api.js@master/weights'
];

let camStream = null;
let detectorEnabled = false;
let modelLoaded = false;

// 카메라 시작
async function startAgeDetection() {
    if (camStream) return;

    try {
        // 카메라 스트림 시작
        camStream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: 'user' },
            audio: false
        });

        console.log('카메라 시작됨');

        // face-api 모델 로드
        if (faceapiAvailable && !modelLoaded) {
            await loadModels();
        }

        // 감지 시작
        if (modelLoaded) {
            detectorEnabled = true;
            runDetection();
        }
    } catch (error) {
        console.error('카메라 시작 실패:', error);
        alert('카메라 권한이 필요합니다.');
    }
}

// face-api 모델 로드
async function loadModels() {
    if (!faceapiAvailable) {
        console.warn('face-api.js가 로드되지 않았습니다');
        return false;
    }

    for (const baseUrl of MODEL_URLS) {
        try {
            console.log(`모델 로딩 시도: ${baseUrl}`);
            await Promise.all([
                faceapi.nets.tinyFaceDetector.loadFromUri(baseUrl),
                faceapi.nets.ageGenderNet.loadFromUri(baseUrl)
            ]);
            modelLoaded = true;
            console.log('모델 로드 성공:', baseUrl);
            return true;
        } catch (error) {
            console.warn(`모델 로드 실패 (${baseUrl}):`, error);
        }
    }

    console.error('모든 모델 로드 시도 실패');
    return false;
}

// 연령 감지 실행
async function runDetection() {
    // 비디오 엘리먼트 생성 (숨김)
    const video = document.createElement('video');
    video.srcObject = camStream;
    video.autoplay = true;
    video.muted = true;
    video.style.display = 'none';
    document.body.appendChild(video);

    // 캔버스 생성 (숨김)
    const canvas = document.createElement('canvas');
    canvas.style.display = 'none';
    document.body.appendChild(canvas);

    while (detectorEnabled && camStream) {
        try {
            if (video.readyState >= 2) {
                // 얼굴 감지 및 연령 추정
                const detection = await faceapi
                    .detectSingleFace(video, new faceapi.TinyFaceDetectorOptions())
                    .withAgeAndGender();

                if (detection && detection.age) {
                    const estimatedAge = Math.round(detection.age);
                    console.log(`추정 연령: ${estimatedAge}세`);

                    // 연령대 결정
                    const ageGroup = getAgeGroup(estimatedAge);

                    // UI 업데이트
                    selectAge(ageGroup);
                }
            }
        } catch (error) {
            console.error('얼굴 감지 오류:', error);
        }

        // 1초마다 감지
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
}

// 연령대 결정
function getAgeGroup(age) {
    if (age <= 12) return 'child';
    if (age <= 19) return 'teen';
    if (age <= 64) return 'adult';
    return 'senior';
}

// 카메라 중지
function stopAgeDetection() {
    detectorEnabled = false;
    if (camStream) {
        camStream.getTracks().forEach(track => track.stop());
        camStream = null;
    }
    console.log('카메라 중지됨');
}

// 자동 시작 (선택사항)
// 페이지 로드 시 자동으로 카메라 시작하려면 주석 해제
// window.addEventListener('load', () => {
//   setTimeout(startAgeDetection, 1000);
// });

// 전역 함수로 노출
window.startAgeDetection = startAgeDetection;
window.stopAgeDetection = stopAgeDetection;
