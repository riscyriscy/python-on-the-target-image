#pragma once
#include <stdint.h>

/* Wire format shared by firmware and host tool: little-endian, packed, 9 bytes. */
typedef struct __attribute__((packed)) {
	uint32_t timestamp_ms;
	int16_t  temperature_cdeg;   /* hundredths of a degree C */
	uint16_t supply_mv;
	uint8_t  status;             /* bit 0: overtemp, bit 1: undervoltage, bit 2: sensor fault */
} telemetry_t;

_Static_assert(sizeof(telemetry_t) == 9, "wire format changed");
