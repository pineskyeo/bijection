#include <stdio.h>
#include <stdlib.h>

int add_numbers(int first_value, int second_value) {
    int total = first_value + second_value;
    return total;
}

int multiply_values(int factor_a, int factor_b) {
    return factor_a * factor_b;
}

int main(void) {
    int result_sum = add_numbers(3, 4);
    int result_product = multiply_values(result_sum, 2);
    printf("Sum: %d\n", result_sum);
    printf("Product: %d\n", result_product);
    return 0;
}
