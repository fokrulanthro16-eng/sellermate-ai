from typing import Optional

from pydantic import BaseModel, Field


class ReviewCreate(BaseModel):
    order_id: str
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = None
    reviewer_name: Optional[str] = None


class ReviewOut(BaseModel):
    id: str
    order_id: str
    order_number: Optional[str]
    customer_id: Optional[str]
    reviewer_name: Optional[str]
    rating: int
    comment: Optional[str]
    created_at: str

    model_config = {"from_attributes": True}


class ReviewStatsOut(BaseModel):
    avg_rating: float
    total_reviews: int
    five_star: int
    four_star: int
    three_star: int
    two_star: int
    one_star: int
