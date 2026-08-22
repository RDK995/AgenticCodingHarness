"""Turn a human title into a URL slug."""


def slugify(text):
    """Return a lowercase, hyphen-separated ASCII slug for `text`."""
    out = []
    for ch in text.lower():
        if ch.isascii() and (ch.isalnum() or ch == "-"):
            out.append(ch)
        elif ch == " ":
            out.append("-")
    slug = "".join(out)
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-")
