#include <iostream>
#include <string>
#include <vector>

class Rectangle {
public:
    Rectangle(double rect_width, double rect_height)
        : rect_width(rect_width), rect_height(rect_height) {}

    double compute_area() const {
        return rect_width * rect_height;
    }

    double compute_perimeter() const {
        return 2.0 * (rect_width + rect_height);
    }

private:
    double rect_width;
    double rect_height;
};

int main() {
    Rectangle my_rect(5.0, 3.0);
    double area_value = my_rect.compute_area();
    double perimeter_value = my_rect.compute_perimeter();
    std::cout << "Area: " << area_value << std::endl;
    std::cout << "Perimeter: " << perimeter_value << std::endl;
    return 0;
}
