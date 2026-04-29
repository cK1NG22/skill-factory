# Intentional BP-033 Leak — Fixture Only

This file deliberately violates BP-033 by reaching into the patterns corpus
directly. Step 4 below names a concrete BP file:

> Read `patterns/bp-007-references.md` for the cited-on-demand rule.

A real phase sub-skill must never do this. The driver materializes BP
content into the input.md pack precisely to avoid this redundant read.
Check 15's Signal 2 should fire on the line above and emit a BLOCKER with
file:line evidence.
