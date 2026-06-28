def clean_text(text: str, max_length: int = 100000) -> str:
    """
    Cleans raw extracted text content:
    - Collapses sequential blank spaces to single spaces.
    - Limits sequential blank lines to at most one empty line.
    - Discards very short junk text lines (e.g. navigation crumbs, single character lines).
    - Retains readable paragraph boundaries.
    - Trims to max_length.
    """
    if not text:
        return ""

    lines = text.splitlines()
    cleaned_lines = []

    for line in lines:
        # Collapse multiple spaces into one and strip
        cleaned_line = " ".join(line.split()).strip()

        # If it's a blank line, add a placeholder empty string to be processed later
        if not cleaned_line:
            cleaned_lines.append("")
            continue

        # Discard junk text lines: length <= 2 and not numeric (like '>', '|', 'x', etc.)
        if len(cleaned_line) <= 2 and not cleaned_line.isdigit():
            continue

        cleaned_lines.append(cleaned_line)

    # Collapse sequential empty lines so that we never have more than one blank line in a row
    final_lines = []
    prev_was_empty = False

    for line in cleaned_lines:
        if line == "":
            if not prev_was_empty:
                final_lines.append("")
                prev_was_empty = True
        else:
            final_lines.append(line)
            prev_was_empty = False

    # Join the lines back together
    cleaned_text = "\n".join(final_lines).strip()

    # Trim to maximum length
    return cleaned_text[:max_length]
