"""
Tests for BitBound expression module.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from bitbound.expression import Expression, parse_expression


class TestExpression:
    """Tests for Expression class."""
    
    def test_simple_greater_than(self):
        expr = Expression("temperature > 25°C")
        assert len(expr.conditions) == 1
        assert expr.conditions[0].property_name == "temperature"
        assert expr.conditions[0].operator == ">"
        assert expr.conditions[0].threshold == 25.0
    
    def test_simple_less_than(self):
        expr = Expression("humidity < 80%")
        assert expr.conditions[0].property_name == "humidity"
        assert expr.conditions[0].operator == "<"
        assert expr.conditions[0].threshold == 80.0
    
    def test_greater_or_equal(self):
        expr = Expression("pressure >= 1000hPa")
        assert expr.conditions[0].operator == ">="
    
    def test_not_equal(self):
        expr = Expression("value != 0")
        assert expr.conditions[0].operator == "!="
    
    def test_evaluate_true(self):
        expr = Expression("temperature > 25°C")
        result = expr.evaluate({"temperature": 30})
        assert result is True
    
    def test_evaluate_false(self):
        expr = Expression("temperature > 25°C")
        result = expr.evaluate({"temperature": 20})
        assert result is False
    
    def test_and_expression(self):
        expr = Expression("temperature > 25°C AND humidity < 80%")
        assert len(expr.conditions) == 2
        assert expr.logical_ops == ["AND"]
    
    def test_or_expression(self):
        expr = Expression("temperature > 30°C OR temperature < 10°C")
        assert len(expr.conditions) == 2
        assert expr.logical_ops == ["OR"]
    
    def test_and_evaluate_true(self):
        expr = Expression("temperature > 25°C AND humidity < 80%")
        result = expr.evaluate({"temperature": 30, "humidity": 50})
        assert result is True
    
    def test_and_evaluate_false(self):
        expr = Expression("temperature > 25°C AND humidity < 80%")
        result = expr.evaluate({"temperature": 30, "humidity": 90})
        assert result is False
    
    def test_or_evaluate_one_true(self):
        expr = Expression("temperature > 30°C OR humidity > 90%")
        result = expr.evaluate({"temperature": 25, "humidity": 95})
        assert result is True
    
    def test_between_expression(self):
        expr = Expression("temperature BETWEEN 20°C AND 25°C")
        assert len(expr.conditions) == 2
    
    def test_between_evaluate_in_range(self):
        expr = Expression("temperature BETWEEN 20°C AND 25°C")
        result = expr.evaluate({"temperature": 22})
        assert result is True
    
    def test_between_evaluate_out_of_range(self):
        expr = Expression("temperature BETWEEN 20°C AND 25°C")
        result = expr.evaluate({"temperature": 30})
        assert result is False
    
    def test_missing_property(self):
        expr = Expression("temperature > 25°C")
        result = expr.evaluate({"humidity": 50})
        assert result is False
    
    def test_get_properties(self):
        expr = Expression("temperature > 25°C AND humidity < 80%")
        props = expr.get_properties()
        assert set(props) == {"temperature", "humidity"}


class TestParseExpression:
    """Tests for parse_expression function."""
    
    def test_parse_returns_expression(self):
        result = parse_expression("temperature > 25°C")
        assert isinstance(result, Expression)
    
    def test_parse_simple(self):
        result = parse_expression("value > 100")
        assert result.evaluate({"value": 150}) is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
