#!/bin/bash

greeting_prefix="Hello"
target_name="World"

say_hello() {
    local user_name="$1"
    local full_greeting="${greeting_prefix}, ${user_name}!"
    echo "$full_greeting"
}

compute_sum() {
    local num_a="$1"
    local num_b="$2"
    local total_result=$((num_a + num_b))
    echo "$total_result"
}

say_hello "$target_name"
sum_output=$(compute_sum 10 20)
echo "Sum is: $sum_output"
