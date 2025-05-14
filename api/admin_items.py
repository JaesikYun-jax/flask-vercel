import json
from .utils import create_response, load_game_items, save_game_items, admin_required

@admin_required
def handler(request, response):
    """관리자용 게임 항목 관리 API"""
    # CORS 프리플라이트 요청 처리
    if request.get('method') == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS"
            }
        }
    
    # 요청 메서드에 따라 처리
    method = request.get('method', 'GET')
    
    try:
        # GET: 게임 항목 목록 조회
        if method == "GET":
            items = load_game_items()
            response_data, status_code = create_response(
                success=True,
                data=items
            )
        
        # POST: 새 게임 항목 추가
        elif method == "POST":
            try:
                body = json.loads(request.get('body', '{}'))
            except:
                body = {}
            
            # 필수 필드 검증
            required_fields = ['title', 'category', 'character_name', 'max_turns', 'win_condition']
            for field in required_fields:
                if field not in body:
                    response_data, status_code = create_response(
                        success=False,
                        error=f"필수 필드가 누락되었습니다: {field}",
                        status_code=400
                    )
                    break
            else:
                # 모든 필수 필드가 있는 경우
                items = load_game_items()
                
                # 새 ID 할당
                new_id = 1
                if items:
                    new_id = max(item['id'] for item in items) + 1
                
                # 새 항목 추가
                new_item = {
                    'id': new_id,
                    'title': body['title'],
                    'category': body['category'],
                    'character_name': body['character_name'],
                    'max_turns': body['max_turns'],
                    'win_condition': body['win_condition']
                }
                
                items.append(new_item)
                
                # 저장
                if save_game_items(items):
                    response_data, status_code = create_response(
                        success=True,
                        data=new_item,
                        message="게임 항목이 추가되었습니다."
                    )
                else:
                    response_data, status_code = create_response(
                        success=False,
                        error="게임 항목 저장 중 오류가 발생했습니다.",
                        status_code=500
                    )
        
        # PUT: 게임 항목 수정
        elif method == "PUT":
            try:
                body = json.loads(request.get('body', '{}'))
            except:
                body = {}
            
            # ID 확인
            item_id = body.get('id')
            if not item_id:
                response_data, status_code = create_response(
                    success=False,
                    error="항목 ID가 필요합니다.",
                    status_code=400
                )
            else:
                items = load_game_items()
                
                # 해당 ID의 항목 찾기
                target_item = next((item for item in items if item['id'] == item_id), None)
                
                if not target_item:
                    response_data, status_code = create_response(
                        success=False,
                        error=f"ID {item_id}인 항목을 찾을 수 없습니다.",
                        status_code=404
                    )
                else:
                    # 항목 업데이트
                    for key in ['title', 'category', 'character_name', 'max_turns', 'win_condition']:
                        if key in body:
                            target_item[key] = body[key]
                    
                    # 저장
                    if save_game_items(items):
                        response_data, status_code = create_response(
                            success=True,
                            data=target_item,
                            message="게임 항목이 업데이트되었습니다."
                        )
                    else:
                        response_data, status_code = create_response(
                            success=False,
                            error="게임 항목 저장 중 오류가 발생했습니다.",
                            status_code=500
                        )
        
        # DELETE: 게임 항목 삭제
        elif method == "DELETE":
            # URL에서 ID 추출
            path = request.get('path', '')
            item_id = None
            
            # 경로 형식: /api/admin/items/123
            if '/items/' in path:
                try:
                    item_id = int(path.split('/items/')[1])
                except:
                    item_id = None
            
            if not item_id:
                response_data, status_code = create_response(
                    success=False,
                    error="삭제할 항목의 ID가 필요합니다.",
                    status_code=400
                )
            else:
                items = load_game_items()
                original_count = len(items)
                
                # 해당 ID의 항목 필터링
                items = [item for item in items if item['id'] != item_id]
                
                if len(items) == original_count:
                    response_data, status_code = create_response(
                        success=False,
                        error=f"ID {item_id}인 항목을 찾을 수 없습니다.",
                        status_code=404
                    )
                else:
                    # 저장
                    if save_game_items(items):
                        response_data, status_code = create_response(
                            success=True,
                            message=f"ID {item_id}인 항목이 삭제되었습니다."
                        )
                    else:
                        response_data, status_code = create_response(
                            success=False,
                            error="게임 항목 저장 중 오류가 발생했습니다.",
                            status_code=500
                        )
        
        # 지원하지 않는 메서드
        else:
            response_data, status_code = create_response(
                success=False,
                error=f"지원하지 않는 메서드: {method}",
                status_code=405
            )
        
        return {
            "statusCode": status_code,
            "body": json.dumps(response_data),
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS"
            }
        }
        
    except Exception as e:
        response_data, status_code = create_response(
            success=False,
            error=str(e),
            status_code=500
        )
        
        return {
            "statusCode": status_code,
            "body": json.dumps(response_data),
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS"
            }
        } 