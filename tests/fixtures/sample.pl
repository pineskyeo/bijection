#!/usr/bin/perl
use strict;
use warnings;

sub compute_factorial {
    my ($input_number) = @_;
    if ($input_number <= 1) {
        return 1;
    }
    return $input_number * compute_factorial($input_number - 1);
}

sub greet_person {
    my ($person_name) = @_;
    my $greeting_text = "Hello, $person_name!";
    print "$greeting_text\n";
    return $greeting_text;
}

my $base_number = 5;
my $factorial_result = compute_factorial($base_number);
print "Factorial of $base_number is $factorial_result\n";
greet_person("Alice");
