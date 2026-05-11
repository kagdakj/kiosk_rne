(function () {
    // face-api.js CDN이 로드되었는지 확인
    const faceapiAvailable = typeof faceapi !== 'undefined';

    const MODEL_URLS = [
        './static/models',
        'https://cdn.jsdelivr.net/gh/justadudewhohacks/face-api.js@master/weights'
    ];

    let camStream = null;
    let detectorEnabled = false;
    let modelLoaded = false;

    // DOM 요소 참조
    const $camOverlay = document.getElementById('camOverlay');
    const $camVideo = document.getElementById('camVideo');
    const $camCanvas = document.getElementById('camCanvas');
    const $camStatusText = document.getElementById('camStatusText');
    const $cameraStatus = document.getElementById('cameraStatus'); // 작은 배지

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

            // 비디오 요소에 스트림 연결
            if ($camVideo) {
                $camVideo.srcObject = camStream;
                // 오버레이 표시
                if ($camOverlay) {
                    $camOverlay.classList.remove('cam-hidden');
                    $camOverlay.setAttribute('aria-hidden', 'false');
                }
            }

            updateStatus('카메라 실행 중...');

            // face-api 모델 로드
            if (faceapiAvailable && !modelLoaded) {
                updateStatus('모델 로딩 중...');
                await loadModels();
            }

            // 감지 시작
            if (modelLoaded) {
                detectorEnabled = true;
                runDetection();
            } else {
                updateStatus('모델 로드 실패');
            }
        } catch (error) {
            console.error('카메라 시작 실패:', error);
            updateStatus('카메라 오류');
            alert('카메라 권한이 필요합니다.');
        }
    }

    // 상태 업데이트 헬퍼
    function updateStatus(text) {
        if ($camStatusText) $camStatusText.textContent = `카메라: ${text}`;
        if ($cameraStatus) $cameraStatus.textContent = `📷 ${text}`;
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
        if (!$camVideo || !$camCanvas) return;

        const ctx = $camCanvas.getContext('2d');

        while (detectorEnabled && camStream) {
            try {
                if ($camVideo.readyState >= 2) {
                    // 캔버스 크기 맞춤
                    $camCanvas.width = $camVideo.videoWidth;
                    $camCanvas.height = $camVideo.videoHeight;
                    ctx.drawImage($camVideo, 0, 0, $camCanvas.width, $camCanvas.height);

                    // 얼굴 감지 및 연령 추정
                    const detection = await faceapi
                        .detectSingleFace($camVideo, new faceapi.TinyFaceDetectorOptions())
                        .withAgeAndGender();

                    if (detection && detection.age) {
                        const estimatedAge = Math.round(detection.age);
                        const ageGroup = getAgeGroup(estimatedAge);

                        updateStatus(`추정 연령: ${estimatedAge}세 (${getAgeGroupName(ageGroup)})`);
                        console.log(`추정: ${estimatedAge}세 -> ${ageGroup}`);

                        // UI 업데이트 (전역 함수 호출)
                        if (typeof selectAge === 'function') {
                            // 너무 잦은 변경 방지 로직이 필요할 수 있음
                            selectAge(ageGroup);
                        }
                    } else {
                        updateStatus('얼굴 찾는 중...');
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

    function getAgeGroupName(group) {
        const names = {
            'child': '어린이',
            'teen': '청소년',
            'adult': '성인',
            'senior': '노인'
        };
        return names[group] || group;
    }

    // 카메라 중지
    function stopAgeDetection() {
        detectorEnabled = false;
        if (camStream) {
            camStream.getTracks().forEach(track => track.stop());
            camStream = null;
        }

        if ($camOverlay) {
            $camOverlay.classList.add('cam-hidden');
            $camOverlay.setAttribute('aria-hidden', 'true');
        }

        updateStatus('비활성');
        console.log('카메라 중지됨');
    }

    // 전역 함수로 노출
    window.startAgeDetection = startAgeDetection;
    window.stopAgeDetection = stopAgeDetection;
})();