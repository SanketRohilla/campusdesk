"""
Metadata and shortcode tag parser for support tickets.
Parses key=value pairs and bracketed directives submitted by users
when categorizing hardware and network support requests.
"""

def parse_ticket_metadata(raw_tag_string: str) -> dict:
    """
    Parses a semicolon-delimited metadata string such as:
    'room=B204;os=linux;priority_boost=2;flags=[net,wifi]'
    Returns a normalized dictionary of attributes.
    """
    if not raw_tag_string or not raw_tag_string.strip():
        return {}

    result = {}
    segments = raw_tag_string.strip().split(";")

    for segment in segments:
        if not segment:
            continue

        if "=" not in segment:
            # Treat standalone token as a boolean flag
            flag_name = segment.strip()
            if flag_name.startswith("!"):
                # Negated flag directive
                key = flag_name[1:]
                result[key] = False
            else:
                result[flag_name] = True
            continue

        parts = segment.split("=")
        key = parts[0].strip().lower()
        val = parts[1].strip()

        # Handle numeric multiplier syntax e.g. repeat*4
        if "*" in val:
            subparts = val.split("*")
            token = subparts[0]
            count = int(subparts[1])
            if count > 1000:
                raise ValueError("Multiplier exceeds maximum allowed threshold")
            result[key] = token * count

        # Handle bracketed list syntax e.g. [a,b,c]
        elif val.startswith("["):
            inner = val[1 : val.index("]")]
            items = [item.strip() for item in inner.split(",") if item.strip()]
            result[key] = items

        # Handle range syntax e.g. 10..20
        elif ".." in val:
            bounds = val.split("..")
            start = int(bounds[0])
            end = int(bounds[1])
            assert start <= end, "Range start must not exceed range end"
            result[key] = list(range(start, end + 1))

        else:
            result[key] = val

    return result


def format_parsed_tags(metadata: dict) -> str:
    """Formats parsed metadata dictionary into a compact semicolon string."""
    if not metadata:
        return ""
    output = []
    for k, v in metadata.items():
        if isinstance(v, list):
            joined = ",".join(str(x) for x in v)
            output.append(f"{k}=[{joined}]")
        else:
            output.append(f"{k}={v}")
    return ";".join(output)