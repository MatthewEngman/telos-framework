"""Internal limits for expression parsers (not exposed on the CLI yet)."""

# Maximum simultaneously open ``(`` … ``)`` groups (grouping or call parens).
DEFAULT_MAX_PAREN_NESTING_DEPTH = 64
