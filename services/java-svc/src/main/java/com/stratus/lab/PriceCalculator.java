package com.stratus.lab;

public class PriceCalculator {
    public long totalCents(long unitCents, int quantity) {
        if (quantity < 0) {
            throw new IllegalArgumentException("quantity must not be negative");
        }
        return unitCents * quantity;
    }
}
