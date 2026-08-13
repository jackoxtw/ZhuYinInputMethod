#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "ZYConversion.h"

static void expect_t2s(ZYConversion *c, const char *input, const char *expected) {
    char out[256];
    assert(zy_conversion_t2s(c, input, out, sizeof(out)) == 0);
    if (strcmp(out, expected) != 0) {
        fprintf(stderr, "t2s mismatch: %s -> %s (expected %s)\n", input, out, expected);
    }
    assert(strcmp(out, expected) == 0);
}

int main(int argc, char **argv) {
    assert(argc == 2);
    ZYConversion c;
    assert(zy_conversion_open(&c, argv[1]) == 0);

    expect_t2s(&c, "臺灣發展", "台湾发展");
    expect_t2s(&c, "後臺", "后台");
    expect_t2s(&c, "麵", "面");
    expect_t2s(&c, "牛肉麵", "牛肉面");
    expect_t2s(&c, "裡面", "里面");
    expect_t2s(&c, "為了", "为了");
    expect_t2s(&c, "著作", "著作");
    expect_t2s(&c, "看著", "看着");

    zy_conversion_close(&c);
    puts("test_conversion: OK");
    return 0;
}
