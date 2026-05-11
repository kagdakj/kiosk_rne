import os
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder='static', static_url_path='/static')
CORS(app)

DATASET_PATH = 'dataset'

@app.route('/')
def index():
    """HTML 페이지 서빙"""
    return send_from_directory('.', 'benchmark.html')

@app.route('/api/dataset', methods=['GET'])
def get_dataset():
    """dataset 폴더에서 모든 이미지를 스캔하고 나이 정보와 함께 반환"""
    images = []
    
    if not os.path.exists(DATASET_PATH):
        return jsonify({'error': f'dataset 폴더를 찾을 수 없습니다. 경로: {os.path.abspath(DATASET_PATH)}'}), 404
    
    # dataset 폴더 내의 숫자 폴더들 순회
    for age_folder in sorted(os.listdir(DATASET_PATH)):
        age_path = os.path.join(DATASET_PATH, age_folder)
        
        if not os.path.isdir(age_path):
            continue
        
        try:
            age = int(age_folder)
        except ValueError:
            continue
        
        # 해당 폴더 내의 이미지 파일 순회
        for filename in sorted(os.listdir(age_path)):
            filepath = os.path.join(age_path, filename)
            
            if not os.path.isfile(filepath):
                continue
            
            ext = os.path.splitext(filename)[1].lower()
            if ext not in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                continue
            
            images.append({
                'filename': filename,
                'age': age,
                'url': f'/dataset/{age_folder}/{filename}'
            })
    
    if not images:
        return jsonify({'error': 'Dataset에 이미지가 없습니다.'}), 404
    
    print(f'✅ {len(images)}개 이미지 발견')
    return jsonify({'images': images, 'total': len(images)})

@app.route('/dataset/<age_folder>/<filename>')
def serve_dataset_image(age_folder, filename):
    """dataset 폴더의 이미지 제공 - 경로 수정"""
    try:
        filepath = os.path.join(DATASET_PATH, age_folder, filename)
        print(f'📸 이미지 요청: {filepath}')
        
        if not os.path.exists(filepath):
            print(f'❌ 파일 없음: {filepath}')
            return jsonify({'error': f'파일 없음: {filepath}'}), 404
        
        return send_from_directory(os.path.join(DATASET_PATH, age_folder), filename)
    except Exception as e:
        print(f'❌ 오류: {str(e)}')
        return jsonify({'error': str(e)}), 404

@app.route('/static/<path:filename>')
def serve_static(filename):
    """정적 파일 서빙"""
    return send_from_directory('static', filename)

@app.route('/benchmark.html', methods=['GET'])
def serve_benchmark():
    """benchmark.html 파일 제공"""
    return send_from_directory('.', 'benchmark.html')

if __name__ == '__main__':
    print('=' * 60)
    print('✅ Flask 벤치마크 서버 시작')
    print('=' * 60)
    print(f'🌐 접속 주소: http://127.0.0.1:5001/benchmark.html')
    print(f'📁 Dataset 경로: {os.path.abspath(DATASET_PATH)}')
    print(f'📂 Static 경로: {os.path.abspath("static")}')
    print(f'📋 현재 디렉토리: {os.getcwd()}')
    print('=' * 60)
    print('종료하려면 Ctrl+C를 누르세요')
    print('=' * 60)
    app.run(host='127.0.0.1', port=5001, debug=False, threaded=True)
