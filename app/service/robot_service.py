from sqlalchemy.orm import Session
from database.crud.robot_log import create_robot_log, read_all_robot_logs
import cv2


def add_robot_log(json_data: dict, db: Session):
    """
    로봇 로그 추가 함수
    Args:
        json_data: 로봇 로그 정보
        db: 데이터베이스 세션
    Returns:
        None
    """
    status_body = json_data.get("OS", {})
    status = status_body.get("status")
    create_robot_log(db, status)


def get_all_logs(db: Session):
    """
    모든 로봇 로그 조회 함수
    Args:
        db: 데이터베이스 세션
    Returns:
        logs: 모든 로봇 로그 리스트
    """
    logs = read_all_robot_logs(db)
    return logs


def get_robot_view():
    """
    로봇 카메라 피드 캡처 함수
    Returns:
        frame: 로봇 카메라 피드 프레임
    """
    cap = cv2.VideoCapture(0)
    try:
        while True:
            success, frame = cap.read()
            if not success:
                break
            else:
                ret, buffer = cv2.imencode(".jpg", frame)
                frame = buffer.tobytes()
                yield (
                    b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
                )
    finally:
        cap.release()
