#pragma once
#include <stddef.h>
#include <stdint.h>

#ifdef _WIN32
#  define CRC16_API __declspec(dllexport)
#else
#  define CRC16_API __attribute__((visibility("default")))
#endif

/* CRC-16/CCITT-FALSE: poly 0x1021, init 0xFFFF, no reflection, no final XOR.
 * The same function the firmware uses to protect each frame. */
CRC16_API uint16_t crc16_ccitt(const uint8_t *data, size_t len);
