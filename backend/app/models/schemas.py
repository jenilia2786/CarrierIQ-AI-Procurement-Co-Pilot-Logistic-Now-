from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# ─── Auth Models ──────────────────────────────────────────────
class UserCreate(BaseModel):
    name: str
    company: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class UserOut(BaseModel):
    id: str
    name: str
    company: str
    email: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserOut

# ─── Carrier Models ───────────────────────────────────────────
class CarrierBidUpload(BaseModel):
    lane: str
    carrier_name: str
    price: float
    transit_days: int
    reliability_pct: float
    user_id: str

class CarrierScore(BaseModel):
    carrier_id: str
    carrier_name: str
    lane: str
    price_score: float
    reliability_score: float
    transit_score: float
    risk_score: float
    total_score: float
    recommendation: str
    reasoning: str

class CarrierProfile(BaseModel):
    carrier_id: str
    name: str
    lanes: List[str]
    on_time_rate: float
    damage_rate: float
    avg_price: float
    mood_index: float
    fraud_score: float
    trust_score: float
    seasonal_data: List[Dict]

# ─── Chat Models ──────────────────────────────────────────────
class ChatQuery(BaseModel):
    query: str
    user_id: str

class ChatResponse(BaseModel):
    answer: str
    reasoning: str
    sources: List[str]
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# ─── RFQ Models ───────────────────────────────────────────────
class RFQRequest(BaseModel):
    origin: str
    destination: str
    cargo_type: str
    weight_kg: float
    volume_cbm: float
    pickup_date: str
    delivery_deadline: str
    special_requirements: Optional[str] = ""
    user_id: str

# ─── Award Letter Models ──────────────────────────────────────
class AwardRequest(BaseModel):
    carrier_name: str
    lane: str
    rate: float
    sla_terms: str
    effective_date: str
    user_id: str

# ─── Scorecard Models ─────────────────────────────────────────
class ScorecardUpdate(BaseModel):
    shipment_id: str
    carrier_id: str
    actual_delivery_date: str
    promised_delivery_date: str
    condition: str  # good / damaged / partial
    billing_accuracy: float  # 0-100
    user_id: str

# ─── Onboarding Scorer ────────────────────────────────────────
class NewCarrierOnboard(BaseModel):
    name: str
    gst_number: str
    vehicle_count: int
    years_in_operation: int
    coverage_cities: List[str]
    certifications: Optional[List[str]] = []
