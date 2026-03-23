"""Sample Python file for bijection testing."""


def calculate_area(width, height):
    """Return the area of a rectangle."""
    result = width * height
    return result


def greet_user(username):
    message = f"Hello, {username}!"
    print(message)
    return message


class ShapeCalculator:
    def __init__(self, default_width, default_height):
        self.default_width = default_width
        self.default_height = default_height

    def compute(self):
        area = calculate_area(self.default_width, self.default_height)
        return area


if __name__ == "__main__":
    calc = ShapeCalculator(5, 10)
    total_area = calc.compute()
    greet_user("world")
    print(total_area)
