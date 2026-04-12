"""
Simple calculator module for demonstrating automated testing plugin.

This module provides basic arithmetic operations and is designed to be used
as a test subject for the Automated Testing Plugin for Claude Code.
"""


def add(a, b):
    """
    Add two numbers together.

    Args:
        a: First number (int or float)
        b: Second number (int or float)

    Returns:
        The sum of a and b

    Examples:
        >>> add(2, 3)
        5
        >>> add(-1, 1)
        0
        >>> add(2.5, 3.7)
        6.2
    """
    return a + b


def subtract(a, b):
    """
    Subtract second number from first number.

    Args:
        a: Number to subtract from (int or float)
        b: Number to subtract (int or float)

    Returns:
        The difference between a and b (a - b)

    Examples:
        >>> subtract(5, 3)
        2
        >>> subtract(10, 15)
        -5
        >>> subtract(7.5, 2.5)
        5.0
    """
    return a - b


def multiply(a, b):
    """
    Multiply two numbers together.

    Args:
        a: First number (int or float)
        b: Second number (int or float)

    Returns:
        The product of a and b

    Examples:
        >>> multiply(3, 4)
        12
        >>> multiply(-2, 5)
        -10
        >>> multiply(2.5, 4)
        10.0
    """
    return a * b


def divide(a, b):
    """
    Divide first number by second number.

    Args:
        a: Numerator (int or float)
        b: Denominator (int or float, must not be zero)

    Returns:
        The quotient of a divided by b

    Raises:
        ValueError: If b is zero

    Examples:
        >>> divide(10, 2)
        5.0
        >>> divide(7, 2)
        3.5
        >>> divide(-10, 2)
        -5.0
        >>> divide(5, 0)
        Traceback (most recent call last):
        ...
        ValueError: Cannot divide by zero
    """
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
