from fastapi import APIRouter, Query
from sqlalchemy import select

from app.core.dependencies import CurrentMerchant, DB
from app.core.exceptions import BadRequestException, ConflictException, NotFoundException
from app.models.order import Order, OrderStatus
from app.models.review import Review
from app.schemas.common import SuccessResponse
from app.schemas.review import ReviewCreate, ReviewOut, ReviewStatsOut

router = APIRouter(tags=["reviews"])


def _to_out(r: Review) -> ReviewOut:
    return ReviewOut(
        id=r.id,
        order_id=r.order_id,
        order_number=r.order_number,
        customer_id=r.customer_id,
        reviewer_name=r.reviewer_name,
        rating=r.rating,
        comment=r.comment,
        created_at=str(r.created_at),
    )


@router.post("", response_model=SuccessResponse[ReviewOut], status_code=201)
async def create_review(body: ReviewCreate, merchant: CurrentMerchant, db: DB):
    order_result = await db.execute(
        select(Order).where(Order.id == body.order_id, Order.merchant_id == merchant.id)
    )
    order = order_result.scalar_one_or_none()
    if not order:
        raise NotFoundException("Order not found")
    if order.status != OrderStatus.DELIVERED:
        raise BadRequestException("Reviews allowed only for delivered orders")

    existing = await db.execute(
        select(Review).where(Review.order_id == body.order_id)
    )
    if existing.scalar_one_or_none():
        raise ConflictException("Review already submitted for this order")

    review = Review(
        merchant_id=merchant.id,
        order_id=body.order_id,
        customer_id=order.customer_id,
        rating=body.rating,
        comment=body.comment,
        reviewer_name=body.reviewer_name,
        order_number=order.order_number,
    )
    db.add(review)
    await db.flush()
    await db.commit()
    await db.refresh(review)
    return SuccessResponse(data=_to_out(review))


@router.get("", response_model=SuccessResponse[list[ReviewOut]])
async def list_reviews(
    merchant: CurrentMerchant,
    db: DB,
    limit: int = Query(50, ge=1, le=100),
):
    result = await db.execute(
        select(Review)
        .where(Review.merchant_id == merchant.id)
        .order_by(Review.created_at.desc())
        .limit(limit)
    )
    rows = result.scalars().all()
    return SuccessResponse(data=[_to_out(r) for r in rows])


@router.get("/stats", response_model=SuccessResponse[ReviewStatsOut])
async def get_review_stats(merchant: CurrentMerchant, db: DB):
    result = await db.execute(
        select(Review).where(Review.merchant_id == merchant.id)
    )
    rows = list(result.scalars().all())
    if not rows:
        return SuccessResponse(data=ReviewStatsOut(
            avg_rating=0.0, total_reviews=0,
            five_star=0, four_star=0, three_star=0, two_star=0, one_star=0,
        ))
    avg = round(sum(r.rating for r in rows) / len(rows), 1)
    return SuccessResponse(data=ReviewStatsOut(
        avg_rating=avg,
        total_reviews=len(rows),
        five_star=sum(1 for r in rows if r.rating == 5),
        four_star=sum(1 for r in rows if r.rating == 4),
        three_star=sum(1 for r in rows if r.rating == 3),
        two_star=sum(1 for r in rows if r.rating == 2),
        one_star=sum(1 for r in rows if r.rating == 1),
    ))
