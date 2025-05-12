import yaml
from .models import (
    MetricFeature, FirstLastFeature, FormulaFeature, FieldFeature,
    conversation_state
)
from pydantic import ValidationError

# Mapping user input to feature types and models
FEATURE_TYPES_MAP = {
    "metric": MetricFeature,
    "first-last": FirstLastFeature,
    "formula": FormulaFeature,
    "field": FieldFeature,
}

# Helper to get required fields from Pydantic model (simplified)
def get_required_fields_for_model(pydantic_model):
    required = []
    if not pydantic_model:
        return required
    for name, field_info in pydantic_model.model_fields.items():
        if field_info.is_required():
            required.append(name)
        elif hasattr(field_info.annotation, 'model_fields'):
             required.append(name)


    # Custom logic for specific fields like 'metric_spec' that are objects
    # We'll prompt for them field by field for a better UX.
    # This initial list helps guide the conversation.
    # A more robust way would be to iterate through the model's schema.
    if pydantic_model == MetricFeature:
        return ["name", "asset_id", "metric_spec"]
    if pydantic_model == FirstLastFeature:
        return ["name", "asset_id", "first_last_spec"]
    if pydantic_model == FormulaFeature:
        return ["name", "formula_spec"]
    if pydantic_model == FieldFeature:
        return ["name", "asset_id", "field_spec"]
    return [f for f in pydantic_model.model_fields.keys() if pydantic_model.model_fields[f].is_required()]


def get_nested_required_fields(parent_field_name, nested_model):
    fields = []
    if not nested_model: return fields
    for name, field_info in nested_model.model_fields.items():
        if field_info.is_required():
            fields.append(f"{parent_field_name}.{name}")
    return fields


def get_initial_prompt():
    conversation_state["current_feature_type"] = None
    conversation_state["collected_data"] = {}
    conversation_state["required_fields"] = []
    conversation_state["model"] = None
    conversation_state["current_question_field"] = None
    conversation_state["awaiting_nested_field_input"] = None
    return "Hello! What type of Lynk feature would you like to create (Metric, First-Last, Formula, or Field)?"


def process_user_message(user_input: str, state: dict):
    user_input_lower = user_input.lower().strip()
    reply = ""
    yaml_output = None

    # 1. If no feature type is selected yet
    if not state.get("current_feature_type"):
        for type_keyword, model in FEATURE_TYPES_MAP.items():
            if type_keyword in user_input_lower:
                state["current_feature_type"] = type_keyword.upper()
                state["model"] = model
                state["collected_data"] = {"type": state["current_feature_type"]}
                
                if model == MetricFeature: state["required_fields"] = ["name", "asset_id", "metric_spec.aggregation", "metric_spec.field", "metric_spec.filter_clause"] # Example
                elif model == FirstLastFeature: state["required_fields"] = ["name", "asset_id", "first_last_spec.operation", "first_last_spec.field", "first_last_spec.order_by_field", "first_last_spec.filter_clause"]
                elif model == FormulaFeature: state["required_fields"] = ["name", "formula_spec.sql"]
                elif model == FieldFeature: state["required_fields"] = ["name", "asset_id", "field_spec.source_field_name"]
                
                state["collected_data"] = {}
                break
        if not state.get("current_feature_type"):
            return "I didn't catch that. Please specify a feature type: Metric, First-Last, Formula, or Field.", None
        # Ask for the first required field
        state["current_question_field"] = state["required_fields"][0]
        reply = f"Great! Let's create a {state['current_feature_type']} feature. What is the '{state['current_question_field']}'?"
        return reply, None

    # 2. Collect data for the current question field
    current_q_field = state.get("current_question_field")
    if current_q_field:
        if '.' in current_q_field:
            parent_key, child_key = current_q_field.split('.', 1)
            if parent_key not in state["collected_data"]:
                state["collected_data"][parent_key] = {}
            if user_input_lower in ["skip", "none", ""]:
                 if not state["model"].model_fields[parent_key].annotation.model_fields[child_key].is_required():
                    state["collected_data"][parent_key][child_key] = None
                 else:
                    return f"The field '{current_q_field}' is required. Please provide a value.", None
            else:
                state["collected_data"][parent_key][child_key] = user_input
        else:
            if user_input_lower in ["skip", "none", ""]:
                if not state["model"].model_fields[current_q_field].is_required():
                    state["collected_data"][current_q_field] = None
                else:
                    return f"The field '{current_q_field}' is required. Please provide a value.", None
            else:
                state["collected_data"][current_q_field] = user_input
        
        # Remove answered field from required_fields (conceptually)
        try:
            state["required_fields"].pop(0)
        except IndexError:
            pass


    # 3. Check if all required fields are collected
    if not state["required_fields"]:
        try:
            # Add the type based on the selected model
            feature_type_literal = state["current_feature_type"]
            if state["model"] == MetricFeature: feature_type_literal = "METRIC"
            elif state["model"] == FirstLastFeature: feature_type_literal = "FIRST_LAST"
            elif state["model"] == FormulaFeature: feature_type_literal = "FORMULA"
            elif state["model"] == FieldFeature: feature_type_literal = "FIELD"

            final_data = {"type": feature_type_literal, **state["collected_data"]}
            
            model_instance = state["model"](**final_data)
            yaml_data = model_instance.model_dump(exclude_none=True, by_alias=True)

            ordered_output = {}
            if 'name' in yaml_data: ordered_output['name'] = yaml_data.pop('name')
            if 'description' in yaml_data: ordered_output['description'] = yaml_data.pop('description')
            ordered_output['type'] = yaml_data.pop('type')
            if 'asset_id' in yaml_data: ordered_output['asset_id'] = yaml_data.pop('asset_id')
            ordered_output.update(yaml_data)

            yaml_output = yaml.dump(ordered_output, sort_keys=False, indent=2)
            reply = "Here is the generated YAML for your feature:"
            get_initial_prompt()
            return reply, yaml_output
        except ValidationError as e:
            # This means some data is invalid or missing despite our checks (e.g. wrong type)
            # More sophisticated error handling would identify which field failed.
            error_messages = "\n".join([f"- {err['loc']}: {err['msg']}" for err in e.errors()])
            reply = f"There was an issue with the provided data:\n{error_messages}\nLet's try again for the problematic fields. Or you can say 'reset'."
            get_initial_prompt()
            reply += "\nState has been reset. What type of feature would you like to create?"
            return reply, None
        except Exception as e:
            reply = f"An unexpected error occurred: {str(e)}. Let's reset."
            get_initial_prompt()
            return reply, None
            
    # 4. Ask for the next required field
    if state["required_fields"]:
        state["current_question_field"] = state["required_fields"][0]
        # Special prompts for certain fields
        prompt_field = state["current_question_field"]
        if prompt_field == "metric_spec.aggregation":
            reply = f"What aggregation do you want for the metric (e.g., COUNT, SUM, AVG, MIN, MAX)?"
        elif prompt_field == "metric_spec.field" and state["collected_data"].get("metric_spec",{}).get("aggregation","").upper() == "COUNT":
            reply = f"For COUNT aggregation, the 'field' is often optional (for COUNT(*)). You can say 'skip' or provide a field name."
        elif prompt_field == "first_last_spec.operation":
            reply = f"Is this a FIRST or LAST operation?"
        elif prompt_field == "formula_spec.sql":
            reply = f"Please provide the SQL for the formula:"
        elif ".filter_clause" in prompt_field:
            reply = f"Provide an optional SQL filter clause for '{prompt_field.split('.')[0]}' (e.g., 'status = \\'active\\''). You can say 'skip' if not needed."
        else:
            reply = f"What is the '{state['current_question_field']}'?"
    else:
        reply = "I'm a bit confused. Let's start over. What type of feature?"
        get_initial_prompt()

    return reply, None