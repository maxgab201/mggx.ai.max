package com.mggx.minecrafttouchhid;

import org.junit.Test;
import java.util.Set;

import static org.junit.Assert.*;

public class ControlMathTest {
    @Test public void deadzoneProducesNoMovement() {
        assertTrue(ControlMath.movementKeys(10f, -10f, 100f).isEmpty());
    }

    @Test public void diagonalsProduceTwoKeys() {
        Set<Integer> keys = ControlMath.movementKeys(60f, -60f, 100f);
        assertEquals(2, keys.size());
        assertTrue(keys.contains(ControlMath.KEY_D));
        assertTrue(keys.contains(ControlMath.KEY_W));
    }

    @Test public void cardinalDirectionsMapCorrectly() {
        assertEquals(Set.of(ControlMath.KEY_A), ControlMath.movementKeys(-80f, 0f, 100f));
        assertEquals(Set.of(ControlMath.KEY_D), ControlMath.movementKeys(80f, 0f, 100f));
        assertEquals(Set.of(ControlMath.KEY_W), ControlMath.movementKeys(0f, -80f, 100f));
        assertEquals(Set.of(ControlMath.KEY_S), ControlMath.movementKeys(0f, 80f, 100f));
    }

    @Test public void clampKeepsMouseReportsInsideSignedByteRange() {
        assertEquals(127, ControlMath.clamp(500, -127, 127));
        assertEquals(-127, ControlMath.clamp(-500, -127, 127));
        assertEquals(42, ControlMath.clamp(42, -127, 127));
    }

    @Test public void mouseSensitivityAndInvertAreApplied() {
        assertEquals(20, ControlMath.scaledMouseDelta(10f, 2f, false));
        assertEquals(-20, ControlMath.scaledMouseDelta(10f, 2f, true));
    }
}
