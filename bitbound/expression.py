"""
Expression parser for declarative threshold conditions.

Parses expressions like "temperature > 25°C" into evaluatable conditions.
"""

import re
import operator
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional, List
from .units import parse_value, Unit


@dataclass
class Condition:
    """A single condition that can be evaluated."""
    property_name: str
    operator: str
    threshold: float
    unit: Optional[Unit]
    
    def evaluate(self, values: Dict[str, Any]) -> bool:
        """
        Evaluate this condition against given values.
        
        Args:
            values: Dictionary of property names to their current values
            
        Returns:
            True if condition is met
        """
        if self.property_name not in values:
            return False
        
        current_value = values[self.property_name]
        
        # Handle Unit comparison
        if isinstance(current_value, Unit):
            current_value = current_value.value
        
        ops = {
            ">": operator.gt,
            "<": operator.lt,
            ">=": operator.ge,
            "<=": operator.le,
            "==": operator.eq,
            "!=": operator.ne,
            "=": operator.eq,
        }
        
        if self.operator not in ops:
            raise ValueError(f"Unknown operator: {self.operator}")
        
        return ops[self.operator](current_value, self.threshold)
    
    def __repr__(self) -> str:
        unit_str = self.unit.symbol if self.unit else ""
        return f"{self.property_name} {self.operator} {self.threshold}{unit_str}"


class Expression:
    """
    Parses and evaluates declarative expressions.
    
    Supports:
        - Simple conditions: "temperature > 25°C"
        - Compound conditions: "temperature > 25°C AND humidity < 80%"
        - Ranges: "temperature BETWEEN 20°C AND 30°C"
    """
    
    # Operators in order of precedence
    COMPARISON_OPS = [">=", "<=", "!=", "==", ">", "<", "="]
    LOGICAL_OPS = ["AND", "OR", "&&", "||", "and", "or"]
    
    def __init__(self, expression: str):
        """
        Initialize with an expression string.
        
        Args:
            expression: String like "temperature > 25°C"
        """
        self.raw_expression = expression
        self.conditions: List[Condition] = []
        self.logical_ops: List[str] = []
        self._parse(expression)
    
    def _parse(self, expression: str) -> None:
        """Parse the expression into conditions and logical operators."""
        # Handle BETWEEN ... AND ... syntax
        between_pattern = r'(\w+)\s+BETWEEN\s+(.+?)\s+AND\s+(.+?)(?:\s+(?:AND|OR|&&|\|\|)|$)'
        between_match = re.search(between_pattern, expression, re.IGNORECASE)
        
        if between_match:
            prop = between_match.group(1)
            low_val, low_unit = parse_value(between_match.group(2).strip())
            high_val, high_unit = parse_value(between_match.group(3).strip())
            
            self.conditions.append(Condition(prop, ">=", low_val, low_unit))
            self.logical_ops.append("AND")
            self.conditions.append(Condition(prop, "<=", high_val, high_unit))
            return
        
        # Split by logical operators
        parts = re.split(r'\s+(AND|OR|&&|\|\|)\s+', expression, flags=re.IGNORECASE)
        
        for i, part in enumerate(parts):
            part = part.strip()
            if part.upper() in ["AND", "OR"] or part in ["&&", "||"]:
                self.logical_ops.append(part.upper().replace("&&", "AND").replace("||", "OR"))
            else:
                condition = self._parse_condition(part)
                if condition:
                    self.conditions.append(condition)
    
    def _parse_condition(self, condition_str: str) -> Optional[Condition]:
        """Parse a single condition string."""
        condition_str = condition_str.strip()
        
        for op in self.COMPARISON_OPS:
            if op in condition_str:
                parts = condition_str.split(op, 1)
                if len(parts) == 2:
                    prop_name = parts[0].strip()
                    value_str = parts[1].strip()
                    
                    try:
                        value, unit = parse_value(value_str)
                        return Condition(prop_name, op, value, unit)
                    except ValueError:
                        # Try as raw number
                        try:
                            value = float(value_str)
                            return Condition(prop_name, op, value, None)
                        except ValueError:
                            pass
        
        return None
    
    def evaluate(self, values: Dict[str, Any]) -> bool:
        """
        Evaluate the expression against given values.
        
        Args:
            values: Dictionary of property names to their current values
            
        Returns:
            True if expression evaluates to true
        """
        if not self.conditions:
            return False
        
        result = self.conditions[0].evaluate(values)
        
        for i, op in enumerate(self.logical_ops):
            if i + 1 < len(self.conditions):
                next_result = self.conditions[i + 1].evaluate(values)
                if op == "AND":
                    result = result and next_result
                elif op == "OR":
                    result = result or next_result
        
        return result
    
    def get_properties(self) -> List[str]:
        """Get list of property names used in this expression."""
        return list(set(c.property_name for c in self.conditions))
    
    def __repr__(self) -> str:
        if not self.conditions:
            return f"Expression({self.raw_expression!r})"
        
        parts = [str(self.conditions[0])]
        for i, op in enumerate(self.logical_ops):
            if i + 1 < len(self.conditions):
                parts.append(op)
                parts.append(str(self.conditions[i + 1]))
        
        return " ".join(parts)


def parse_expression(expr_string: str) -> Expression:
    """
    Parse an expression string into an Expression object.
    
    Args:
        expr_string: Expression like "temperature > 25°C AND humidity < 80%"
        
    Returns:
        Expression object
    """
    return Expression(expr_string)
