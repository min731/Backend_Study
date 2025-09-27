# modules/business_logic.py
import logging

# 로거 이름이 'my_app.business_logic'가 됩니다.
logger = logging.getLogger("my_app.business_logic")

def process_data(item_id: str):
    logger.info(f"데이터 처리 시작: item_id={item_id}")
    # ... 복잡한 데이터 처리 로직이 있다고 가정 ...
    if item_id == "error":
        logger.warning("처리 중 잠재적인 문제 발견")
        raise ValueError("잘못된 아이템 ID입니다.")
    
    logger.debug("데이터 처리 중간 단계 완료")
    logger.info("데이터 처리 성공")
    return {"status": "success", "item_id": item_id}