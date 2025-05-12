from pydantic import BaseModel, Field as PydanticField
from typing import Optional, Literal, Dict, Any

class BaseLynkFeature(BaseModel):
    name: str
    description: Optional[str] = None

class MetricSpec(BaseModel):
    aggregation: str  # e.g., COUNT, SUM, AVG, MIN, MAX
    field: Optional[str] = None # Required for SUM, AVG, etc. but not for COUNT(*)
    filter_clause: Optional[str] = None

class MetricFeature(BaseLynkFeature):
    type: Literal["METRIC"] = "METRIC"
    asset_id: str
    metric_spec: MetricSpec

class FirstLastSpec(BaseModel):
    operation: Literal["FIRST", "LAST"] # To distinguish between First and Last
    field: str # The field whose first/last value is sought
    order_by_field: str # The field to determine order
    filter_clause: Optional[str] = None
    order_by_type: Literal["ASC", "DESC"]

class FirstLastFeature(BaseLynkFeature):
    type: Literal["FIRST_LAST"] # Or whatever the actual YAML 'type' key is for this
    asset_id: str
    first_last_spec: FirstLastSpec

class FormulaSpec(BaseModel):
    sql: str

class FormulaFeature(BaseLynkFeature):
    type: Literal["FORMULA"] = "FORMULA"
    formula_spec: FormulaSpec

class FieldSpec(BaseModel):
    source_field_name: str # the asset

class FieldFeature(BaseLynkFeature):
    type: Literal["FIELD"] = "FIELD"
    asset_id: str
    field_spec: FieldSpec

# A dictionary to hold current feature building state
# This would be managed per user session in a real multi-user app
# For simplicity, we can start with a global state for a single-user demo.
conversation_state = {
    "current_feature_type": None, # "METRIC", "FIRST_LAST", etc.
    "collected_data": {},
    "required_fields": [],
    "model": None # Pydantic model for the current feature type
}