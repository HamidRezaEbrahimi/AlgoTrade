import os
import glob
from typing import Any

from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel

from app.strategy.patterns.rule_engine import get_pattern_rules as engine_get_pattern_rules, invalidate_rules_cache

router = APIRouter(prefix="/config", tags=["config"])

CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config", "patterns")

class RuleUpdatePayload(BaseModel):
    patterns: list[dict[str, Any]]
    ratios: list[dict[str, Any]] | None = None
    thresholds: list[dict[str, Any]] | None = None
    detector_config: dict[str, Any] | None = None

from app.strategy.alef_config import (
    build_alef_rules_payload,
    load_alef_trade_config,
    save_alef_trade_config,
)

@router.get("/pattern-rules")
async def get_pattern_rules():
    """Return the AlefTrade pattern configurations formatted for the UI."""
    try:
        patterns = build_alef_rules_payload()
        alef_cfg = load_alef_trade_config()
        return {
            "patterns": patterns,
            "alef_config": alef_cfg,
            "detector_config": alef_cfg.get("running_flat", {}),
        }
    except Exception as e:
        logger.warning("Falling back to engine rules: %s", e)
        patterns = engine_get_pattern_rules()
        return {"patterns": patterns, "detector_config": {}}

import ruamel.yaml

@router.post("/pattern-rules")
async def update_pattern_rules(payload: RuleUpdatePayload = Body(...)):
    """Update AlefTrade configuration and pattern rules from UI payload."""
    try:
        # 1. Update live AlefTrade engine configuration
        alef_updates: dict[str, Any] = {}
        for p in payload.patterns:
            cat = p.get("category")
            if not cat:
                continue
            if cat not in alef_updates:
                alef_updates[cat] = {}
            for r in p.get("ratios", []):
                k = r.get("key")
                v = r.get("typical", r.get("value"))
                if k is not None and v is not None:
                    try:
                        alef_updates[cat][k] = float(v)
                    except (ValueError, TypeError):
                        pass
            for t in p.get("thresholds", []):
                k = t.get("key")
                v = t.get("typical", t.get("value"))
                if k is not None and v is not None:
                    try:
                        alef_updates[cat][k] = float(v)
                    except (ValueError, TypeError):
                        pass

        if alef_updates:
            save_alef_trade_config(alef_updates)

        # 2. Sync to YAML files where applicable
        grouped = {}
        for p in payload.patterns:
            cat = p.get("category")
            if not cat: continue
            if cat not in grouped:
                grouped[cat] = {"bullish": [], "bearish": [], "ratios": None, "thresholds": None}
            d = p.get("direction", "bullish")
            grouped[cat][d] = p.get("rules", [])
            if p.get("ratios") is not None:
                grouped[cat]["ratios"] = p.get("ratios")
            if p.get("thresholds") is not None:
                grouped[cat]["thresholds"] = p.get("thresholds")
        
        ryaml = ruamel.yaml.YAML()
        ryaml.preserve_quotes = True
        
        for cat, directions in grouped.items():
            file_path = os.path.join(CONFIG_DIR, f"{cat}.yaml")
            if not os.path.exists(file_path):
                continue
                
            with open(file_path, "r", encoding="utf-8") as f:
                data = ryaml.load(f)
                
            if "rules" not in data:
                data["rules"] = {}
                
            # We must rebuild the rules structure from the payload.
            # We'll map them back by their group (e.g. 'structure', 'ratios').
            merged_groups = {}
            bullish_rules = directions["bullish"]
            bearish_rules = directions["bearish"]
            
            # Since the UI generates rules with a specific group, we can group them.
            # To handle differences between bullish and bearish:
            all_rule_ids = set([r.get("rule_id") for r in bullish_rules] + [r.get("rule_id") for r in bearish_rules])
            
            for rid in all_rule_ids:
                bull_r = next((r for r in bullish_rules if r.get("rule_id") == rid), None)
                bear_r = next((r for r in bearish_rules if r.get("rule_id") == rid), None)
                
                # Assume group and description from whichever exists
                base_r = bull_r or bear_r
                grp = base_r.get("group", "structure")
                if grp not in merged_groups:
                    merged_groups[grp] = []
                    
                bull_cel = bull_r.get("var_left") if bull_r and bull_r.get("operator") == "expr_cel" else (bull_r.get("condition") if bull_r else None)
                bear_cel = bear_r.get("var_left") if bear_r and bear_r.get("operator") == "expr_cel" else (bear_r.get("condition") if bear_r else None)
                
                # If the UI generates "var_left" as the raw cel string and "operator" as "expr_cel", we use var_left.
                # If they used the visual builder, condition has the expression (e.g. features.ratios.b_over_a <= 0.8)
                def compile_cel(r):
                    if not r: return None
                    if r.get("operator") == "expr_cel":
                        return r.get("var_left")
                    # Visual builder: replace UI vars with CEL features
                    # This is simplified: if UI gives "p4_price >= p0_price", we might just save it as is.
                    # We expect the UI to build valid CEL in `condition`
                    return r.get("condition")
                
                bull_cel = compile_cel(bull_r)
                bear_cel = compile_cel(bear_r)
                
                final_cel = ""
                if bull_cel == bear_cel and bull_cel:
                    final_cel = bull_cel
                elif bull_cel and bear_cel:
                    final_cel = f'(direction == "bullish" && ({bull_cel})) || (direction == "bearish" && ({bear_cel}))'
                elif bull_cel:
                    final_cel = f'direction == "bullish" && ({bull_cel})'
                elif bear_cel:
                    final_cel = f'direction == "bearish" && ({bear_cel})'
                    
                if final_cel:
                    merged_groups[grp].append({
                        "id": rid,
                        "expr_cel": final_cel,
                        "title_fa": base_r.get("description", ""),
                        "title_en": base_r.get("description", ""),
                        "severity": "fail"
                    })
            
            # Now update the ruamel data
            for grp, rules in merged_groups.items():
                data["rules"][grp] = rules
            
            if "numbers" not in data:
                data["numbers"] = {}
                
            if directions.get("ratios") is not None:
                data["numbers"]["ratios"] = directions["ratios"]
                
            if directions.get("thresholds") is not None:
                data["numbers"]["thresholds"] = directions["thresholds"]
                
            with open(file_path, "w", encoding="utf-8") as f:
                ryaml.dump(data, f)
                
        invalidate_rules_cache()
        return {"status": "success", "message": "Pattern rules updated successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating pattern rules: {str(e)}") from e

@router.get("/patterns/{pattern_key}/raw")
async def get_pattern_raw(pattern_key: str):
    """Return the raw YAML content of a pattern."""
    file_path = os.path.join(CONFIG_DIR, f"{pattern_key}.yaml")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Pattern file not found")
    with open(file_path, "r", encoding="utf-8") as f:
        return {"yaml": f.read()}

class RawUpdatePayload(BaseModel):
    yaml_content: str

import yaml

@router.post("/patterns/{pattern_key}/raw")
async def update_pattern_raw(pattern_key: str, payload: RawUpdatePayload = Body(...)):
    """Update the raw YAML file of a pattern."""
    file_path = os.path.join(CONFIG_DIR, f"{pattern_key}.yaml")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Pattern file not found")
        
    try:
        data = yaml.safe_load(payload.yaml_content)
        if "pattern" not in data:
            raise ValueError("Missing 'pattern' key in YAML")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid YAML format: {str(e)}")
        
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(payload.yaml_content)
        
    invalidate_rules_cache()
    return {"status": "success", "message": "Pattern rules updated successfully."}
