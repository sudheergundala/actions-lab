package com.stratus.lab;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import org.junit.jupiter.api.Test;

class PriceCalculatorTest {
    private final PriceCalculator calc = new PriceCalculator();

    @Test
    void multipliesUnitPriceByQuantity() {
        assertEquals(2501L, calc.totalCents(1250L, 2));
    }

    @Test
    void rejectsNegativeQuantity() {
        assertThrows(IllegalArgumentException.class, () -> calc.totalCents(1250L, -1));
    }
}
