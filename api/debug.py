"""
디버그 정보 API 엔드포인트
"""
import json
import os
import sys
import platform

def handle(request, context):
    """
    서버 디버그 정보 API
    """
    # CORS 헤더
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Content-Type': 'application/json'
    }
    
    # OPTIONS 요청(CORS preflight) 처리
    if request.get('method', '') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': ''
        }
    
    try:
        # 디버그 정보 수집
        debug_info = {
            'python_version': sys.version,
            'platform': platform.platform(),
            'env_vars': {k: v for k, v in os.environ.items() 
                        if not k.startswith('AWS_') 
                        and not 'SECRET' in k.upper() 
                        and not 'KEY' in k.upper()},
            'request_info': {
                'method': request.get('method', 'unknown'),
                'path': request.get('path', 'unknown'),
                'headers': request.get('headers', {}),
                'query': request.get('queryStringParameters', {})
            },
            'context': str(context) if context else "None"
        }
        
        # 파일 시스템 정보 수집 시도
        try:
            debug_info['current_dir'] = os.getcwd()
            debug_info['dir_listing'] = os.listdir('.')
            if os.path.exists('./api'):
                debug_info['api_dir_listing'] = os.listdir('./api')
        except Exception as fs_err:
            debug_info['filesystem_error'] = str(fs_err)
            
        body = json.dumps({
            'success': True,
            'data': debug_info
        })
        
    except Exception as e:
        body = json.dumps({
            'success': False,
            'error': str(e)
        })
    
    # 응답 반환
    return {
        'statusCode': 200,
        'headers': headers,
        'body': body
    } 