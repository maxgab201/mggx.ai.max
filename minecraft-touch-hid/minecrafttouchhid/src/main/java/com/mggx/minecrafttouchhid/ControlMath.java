package com.mggx.minecrafttouchhid;

import java.util.HashSet;
import java.util.Set;

/** Pure input math kept Android-free so behavior can be unit tested on the JVM. */
public final class ControlMath {
    public static final int KEY_A = 0x04;
    public static final int KEY_D = 0x07;
    public static final int KEY_S = 0x16;
    public static final int KEY_W = 0x1A;

    private ControlMath() {}

    public static int clamp(int value, int min, int max) {
        return Math.max(min, Math.min(max, value));
    }

    public static Set<Integer> movementKeys(float dx, float dy, float radius) {
        float threshold = radius * 0.28f;
        Set<Integer> movement = new HashSet<>();
        if (dx < -threshold) movement.add(KEY_A);
        if (dx > threshold) movement.add(KEY_D);
        if (dy < -threshold) movement.add(KEY_W);
        if (dy > threshold) movement.add(KEY_S);
        return movement;
    }

    public static int scaledMouseDelta(float raw, float sensitivity, boolean invert) {
        return Math.round(raw * sensitivity * (invert ? -1f : 1f));
    }
}
