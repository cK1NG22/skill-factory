# Intentional meta-BP citation — fixture only

This file exists to test Check 14. It cites `bp-028` and also references
the path `patterns/meta/bp-028-blocker-convention.md`. Either hit should
cause `skill-compliance-gate` to emit a BLOCKER.

In a real client skill, a citation like this would indicate that factory-
internal mechanics leaked into a user-facing reference file. The correct
fix is to rewrite the reference using domain-level language — end users
should not need to think about factory BPs.
