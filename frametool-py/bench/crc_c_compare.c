/* Bitwise and table-driven CRC-16/CCITT-FALSE in C, timed on 1 MiB: the like-for-like
 * comparison for the Python CRC in frametool. Build: gcc -O2 -o crc_c_compare crc_c_compare.c */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#define SIZE (1u << 20)
#define RUNS 5

static uint16_t table[256];

static uint16_t crc16_bitwise(const uint8_t *data, size_t len)
{
    uint16_t crc = 0xFFFF;
    while (len--) {
        crc ^= (uint16_t)(*data++ << 8);
        for (int bit = 0; bit < 8; bit++)
            crc = (crc & 0x8000) ? (uint16_t)((crc << 1) ^ 0x1021) : (uint16_t)(crc << 1);
    }
    return crc;
}

static void build_table(void)
{
    for (int i = 0; i < 256; i++) {
        uint16_t crc = (uint16_t)(i << 8);
        for (int bit = 0; bit < 8; bit++)
            crc = (crc & 0x8000) ? (uint16_t)((crc << 1) ^ 0x1021) : (uint16_t)(crc << 1);
        table[i] = crc;
    }
}

static uint16_t crc16_table(const uint8_t *data, size_t len)
{
    uint16_t crc = 0xFFFF;
    while (len--)
        crc = (uint16_t)((crc << 8) ^ table[(crc >> 8) ^ *data++]);
    return crc;
}

static double best_ms(uint16_t (*fn)(const uint8_t *, size_t), const uint8_t *data, uint16_t *out)
{
    double best = 1e9;
    for (int run = 0; run < RUNS; run++) {
        struct timespec a, b;
        clock_gettime(CLOCK_MONOTONIC, &a);
        *out = fn(data, SIZE);
        clock_gettime(CLOCK_MONOTONIC, &b);
        double ms = (double)(b.tv_sec - a.tv_sec) * 1e3 + (double)(b.tv_nsec - a.tv_nsec) / 1e6;
        if (ms < best)
            best = ms;
    }
    return best;
}

int main(void)
{
    uint8_t *image = malloc(SIZE);
    uint16_t crc_bit, crc_tab;
    if (!image)
        return 1;
    for (uint32_t i = 0; i < SIZE; i++)
        image[i] = (uint8_t)(i * 31u);  /* the same image as crc_bench.py */
    build_table();
    double bitwise = best_ms(crc16_bitwise, image, &crc_bit);
    double tabled = best_ms(crc16_table, image, &crc_tab);
    printf("1 MiB image, best of %d runs, crc %04X and %04X\n", RUNS, crc_bit, crc_tab);
    printf("  C bitwise       %6.2f ms\n  C table driven  %6.2f ms\n", bitwise, tabled);
    free(image);
    return crc_bit == crc_tab ? 0 : 1;
}
