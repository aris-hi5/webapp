from datetime import datetime
from fastapi import APIRouter, Request, Form, Depends, HTTPException
from matplotlib.dates import DayLocator, DateFormatter, date2num
from matplotlib import font_manager, rc
from sqlalchemy.orm import Session
from starlette.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from database.database import get_db
from service import item_service, robot_service, sales_service, order_service
from auth.auth import manager
import matplotlib.pyplot as plt
import io
import base64

router = APIRouter()
templates = Jinja2Templates(directory="app/resource/templates")


@router.get("/log", dependencies=[Depends(manager)])
def show_logs(request: Request, db: Session = Depends(get_db)):
    """
    로그 조회 API
    Args:
        request: Request 객체
        db: 데이터베이스 세션
    Returns:
        모든 로그 정보 리스트 반환 (HTML)
    """
    logs = robot_service.get_all_logs(db)
    return templates.TemplateResponse("log.html", {"request": request, "logs": logs})


@router.get("/stock", dependencies=[Depends(manager)])
def show_inventory(request: Request, db: Session = Depends(get_db)):
    """
    재고 조회 API
    Args:
        request: Request 객체
        db: 데이터베이스 세션
    Returns:
        모든 재고 정보 리스트 반환 (HTML)
    """
    ice_creams, toppings, consumables = item_service.get_all_inventories(db)
    return templates.TemplateResponse(
        "stock.html",
        {
            "request": request,
            "inventory_data": {
                "ice_cream": ice_creams,
                "topping": toppings,
                "consumable": consumables,
            },
        },
    )


@router.get("/history", dependencies=[Depends(manager)])
def show_history(request: Request, db: Session = Depends(get_db)):
    """
    주문 내역 조회 API
    Args:
        request: Request 객체
        db: 데이터베이스 세션
    Returns:
        모든 주문 내역 리스트 반환 (HTML)
    """
    orders = order_service.get_all_histories(db)
    return templates.TemplateResponse(
        "history.html", {"request": request, "orders": orders}
    )


# 한글 폰트 설정
font_path = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
font_manager.fontManager.addfont(font_path)
rc("font", family="NanumGothic")


@router.get("/sales", response_class=HTMLResponse, dependencies=[Depends(manager)])
def show_sales(request: Request, db: Session = Depends(get_db)):
    """
    매출 조회 API
    Args:
        request: Request 객체
        db: 데이터베이스 세션
    Returns:
        일별 총 매출 및 아이스크림 매출량 그래프 (HTML)
    """
    sales_data = sales_service.get_sales_data(db)
    dates, choco_sales, mint_sales, strawberry_sales = (
        sales_service.process_data_for_sales(sales_data)
    )
    dates_volumes, choco_volumes, mint_volumes, strawberry_volumes = (
        sales_service.process_data_for_volumes(sales_data)
    )

    # 날짜 형식 변환
    formatted_dates = [datetime.strptime(date, "%Y-%m-%d") for date in dates]
    formatted_date_strings = [date.strftime("%m/%d") for date in formatted_dates]

    # 총 매출액 계산
    total_sales = [
        choco_sales[i] + mint_sales[i] + strawberry_sales[i] for i in range(len(dates))
    ]

    # 공통 DayLocator 및 DateFormatter 설정
    day_locator = DayLocator(interval=5)
    date_formatter = DateFormatter("%m/%d")

    # 첫 번째 그래프: 일자별 총매출액 꺾쇠 그래프
    fig, ax1 = plt.subplots(figsize=(12, 6))  # 창 크기를 키움
    ax1.plot(formatted_dates, total_sales, label="총 매출", color="black", linewidth=3)

    for i, date in enumerate(formatted_dates):
        ax1.annotate(
            f"{total_sales[i]}",
            (date, total_sales[i]),
            textcoords="offset points",
            xytext=(0, 10),
            ha="center",
        )

    ax1.set_xlabel("날짜")
    ax1.set_ylabel("총 매출")
    ax1.set_title("일별 총 매출")
    ax1.legend()
    ax1.tick_params(axis="x")

    # 5일 간격으로 주요 눈금 설정
    ax1.xaxis.set_major_locator(day_locator)
    ax1.xaxis.set_major_formatter(date_formatter)

    # 작은 눈금 설정
    ax1.xaxis.set_minor_locator(DayLocator(interval=1))
    ax1.tick_params(which="minor", length=5, direction="inout", bottom=True)

    plt.subplots_adjust(
        top=0.85
    )  # 상단 여백을 조정하여 라벨이 그래프 창을 넘어가지 않도록 함

    plt.tight_layout()
    png_image_total_sales = io.BytesIO()
    plt.savefig(png_image_total_sales, format="png", transparent=False)
    png_image_total_sales_b64_string = "data:image/png;base64," + base64.b64encode(
        png_image_total_sales.getvalue()
    ).decode("utf8")
    plt.close()

    # 두 번째 그래프: 일자별 각각의 아이스크림 매출량 막대그래프
    fig, ax2 = plt.subplots(figsize=(12, 6))  # 창 크기를 키움

    bar_width = 0.2
    bar_positions = date2num(formatted_dates)

    ax2.bar(
        bar_positions - bar_width,
        choco_volumes,
        width=bar_width,
        label="초코",
        color="saddlebrown",
    )
    ax2.bar(bar_positions, mint_volumes, width=bar_width, label="민트", color="cyan")
    ax2.bar(
        bar_positions + bar_width,
        strawberry_volumes,
        width=bar_width,
        label="딸기",
        color="hotpink",
    )

    ax2.set_xlabel("날짜")
    ax2.set_ylabel("매출량")
    ax2.set_title("일별 아이스크림 매출량")
    ax2.legend()
    ax2.tick_params(axis="x")

    # 5일 간격으로 주요 눈금 설정
    ax2.xaxis.set_major_locator(day_locator)
    ax2.xaxis.set_major_formatter(date_formatter)

    # 작은 눈금 설정
    ax2.xaxis.set_minor_locator(DayLocator(interval=1))
    ax2.tick_params(which="minor", length=5, direction="inout", bottom=True)

    plt.tight_layout()
    png_image_icecream_sales = io.BytesIO()
    plt.savefig(png_image_icecream_sales, format="png", transparent=False)
    png_image_icecream_sales_b64_string = "data:image/png;base64," + base64.b64encode(
        png_image_icecream_sales.getvalue()
    ).decode("utf8")
    plt.close()

    return templates.TemplateResponse(
        "sales.html",
        {
            "request": request,
            "total_sales_data": png_image_total_sales_b64_string,
            "icecream_sales_data": png_image_icecream_sales_b64_string,
        },
    )


@router.get("/item", dependencies=[Depends(manager)])
def show_item(request: Request, db: Session = Depends(get_db)):
    """
    아이템 조회 API
    Args:
        request: Request 객체
        db: 데이터베이스 세션
    Returns:
        모든 아이템 정보 리스트 반환 (HTML)
    """
    ice_creams, toppings, consumables = item_service.get_all_items(db)
    return templates.TemplateResponse(
        "item.html",
        {
            "request": request,
            "ice_creams": ice_creams,
            "toppings": toppings,
            "consumables": consumables,
        },
    )


@router.post("/item", dependencies=[Depends(manager)])
def add_item(
    request: Request,
    item_type: str = Form(...),
    item_name: str = Form(...),
    item_price: int = Form(...),
    item_quantity: int = Form(...),
    db: Session = Depends(get_db),
):
    """
    아이템 추가 API
    Args:
        item_type: 아이템 타입
        item_name: 아이템 이름
        item_price: 아이템 가격
        item_quantity: 아이템 수량
        db: 데이터베이스 세션
    Returns:
        모든 아이템 정보 리스트 반환 (JSON)
    """
    item_service.add_item(item_type, item_name, item_price, item_quantity, db)
    return item_service.get_all_items(db)


@router.delete("/item/{item_type}/{item_id}", dependencies=[Depends(manager)])
def remove_item(item_type: str, item_id: int, db: Session = Depends(get_db)):
    """
    아이템 삭제 API
    Args:
        item_type: 아이템 타입
        item_id: 아이템 ID
        db: 데이터베이스 세션
    Returns:
        아이템 삭제 성공 여부 (JSON)
    """
    if item_service.remove_item(item_type, item_id, db):
        return {"success": True}
    else:
        return {"success": False}


@router.get("/camera_feed", dependencies=[Depends(manager)])
def camera_feed():
    """
    카메라 피드 조회 API
    Returns:
        카메라 피드를 반환 (MJPEG)
    """
    return StreamingResponse(
        robot_service.get_robot_view(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@router.get("/camera", dependencies=[Depends(manager)], response_class=HTMLResponse)
def show_camera(request: Request):
    """
    카메라 화면 조회 API
    Args:
        request: Request 객체
    Returns:
        카메라 화면 (HTML)
    """
    return templates.TemplateResponse("camera.html", {"request": request})
