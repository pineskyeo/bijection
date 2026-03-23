# Sample Documentation

This document demonstrates bijection on Markdown files with code blocks.

## Python Example

```python
def compute_fibonacci(sequence_length):
    first_value = 0
    second_value = 1
    result_list = []
    for iteration_count in range(sequence_length):
        result_list.append(first_value)
        first_value, second_value = second_value, first_value + second_value
    return result_list
```

## C Example

```c
int compute_max(int value_a, int value_b) {
    if (value_a > value_b) {
        return value_a;
    }
    return value_b;
}
```

## Regular text is not transformed

This paragraph contains words like `function` and `variable` but they
are plain text, not code, so they should not be transformed.
