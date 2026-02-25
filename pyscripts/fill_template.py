"""
fill_template.py
----------------
Fills a .vsdx template by performing token substitution on page1.xml,
then repackages the result as a new .vsdx file.

Usage:
    python fill_template.py --data data.json --out filled.vsdx [--no-scrub]

The data JSON should be a flat key-value object where keys match the
[BracketedTokens] already present in the Visio template, e.g.:
    {
        "Client1FullName": "John Smith",
        "Client1Executor": "Jane Smith",
        ...
    }

Tokens absent from the JSON (or with null/empty values) are replaced with
an empty string. --scrub (on by default) then removes visual lines that
are entirely empty after substitution, so no ghost label lines appear.

The script ONLY replaces text content and newlines — it never touches XML
tags, attributes, or structural elements, making it safe for old Visio versions.
"""

import argparse
import io
import json
import re
import zipfile
from pathlib import Path


TEMPLATE_VSDX = Path(__file__).parent.parent / "assets" / "Estate Plan Flow Template with Structure.vsdx"
PAGE_PATHS = ["visio/pages/page1.xml"]  # extend if multi-page

# Characters that count as "nothing" when deciding if a line is empty.
# A line whose visible content is only these chars (after stripping XML tags)
# will be removed by the scrubber.
_EMPTY_LINE_CHARS = re.compile(r'^[\s:•\-/]+$')
_XML_TAG = re.compile(r'<[^>]+/>')


def load_data(json_path: str) -> dict:
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def substitute_tokens(xml_text: str, data: dict) -> tuple[str, list[str], list[str]]:
    """
    Replace all [Key] tokens in xml_text.
    - Keys present with a non-empty value → substituted normally.
    - Keys present with null/empty value, or absent entirely → replaced with "".
    Returns (modified_xml, replaced_keys, zeroed_keys).
    """
    replaced = []
    zeroed = []

    # First collect all tokens that exist in the XML
    all_tokens = set(re.findall(r'\[([A-Za-z][A-Za-z0-9_]*)\]', xml_text))

    for key in all_tokens:
        token = f"[{key}]"
        value = data.get(key)

        if value:  # non-empty string
            safe_value = (
                str(value)
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace("'", "&apos;")
                .replace('"', "&quot;")
            )
            xml_text = xml_text.replace(token, safe_value)
            replaced.append(key)
        else:
            # Missing or empty — zero out the token text
            xml_text = xml_text.replace(token, "")
            zeroed.append(key)

    return xml_text, replaced, zeroed


def scrub_empty_lines(xml_text: str) -> tuple[str, int]:
    """
    Within each <Text>...</Text> block, remove visual lines that have XML
    formatting tags but no visible alphanumeric content left (e.g. a label
    like "Successor Executor: " with an emptied value token).

    Safe rules:
    - Never removes or modifies XML tags themselves.
    - Only removes the newline that would create the blank visual line,
      and any inter-tag text that is purely punctuation/whitespace.
    - Bare newlines with no XML tags (intentional blank spacing) are preserved.

    Returns (scrubbed_xml, count_of_lines_removed).
    """
    removed_count = [0]

    def scrub_block(match: re.Match) -> str:
        inner = match.group(1)
        segments = inner.split('\n')
        out = []

        for seg in segments:
            has_tags = bool(_XML_TAG.search(seg))
            visible = _XML_TAG.sub('', seg)  # strip XML tags → visible text only

            if has_tags and (not visible.strip() or _EMPTY_LINE_CHARS.match(visible.strip())):
                # Line has structure tags but no real content.
                # Keep the tags but drop the surrounding newline by not appending \n.
                # Strip any residual inter-tag label text too.
                tags_only = re.sub(r'(?<=>)[^<\n]+(?=<)', '', seg)
                # Append inline (no newline) so it merges invisibly with adjacent run.
                if out:
                    out[-1] = out[-1] + tags_only
                else:
                    out.append(tags_only)
                removed_count[0] += 1
            else:
                out.append(seg)

        return '<Text>' + '\n'.join(out) + '</Text>'

    result = re.sub(r'<Text>(.*?)</Text>', scrub_block, xml_text, flags=re.DOTALL)
    return result, removed_count[0]


def fill_template_bytes(
    data: dict,
    template_bytes: bytes,
    scrub: bool = True,
    page_paths: list[str] = PAGE_PATHS,
) -> tuple[bytes, dict]:
    """
    Core in-memory transformer. Accepts the template as raw bytes and returns
    the filled .vsdx as raw bytes plus a summary dict for logging.

    This is the function called by both the CLI and the Azure Function —
    no filesystem access, no side effects.
    """
    all_replaced: list[str] = []
    all_zeroed: list[str] = []
    total_scrubbed = 0

    in_buf = io.BytesIO(template_bytes)
    out_buf = io.BytesIO()

    with zipfile.ZipFile(in_buf, "r") as zin:
        with zipfile.ZipFile(out_buf, "w", compression=zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                content = zin.read(item.filename)

                if item.filename in page_paths:
                    xml_text = content.decode("utf-8")
                    xml_text, replaced, zeroed = substitute_tokens(xml_text, data)
                    all_replaced.extend(replaced)
                    all_zeroed.extend(zeroed)

                    if scrub:
                        xml_text, n_scrubbed = scrub_empty_lines(xml_text)
                        total_scrubbed += n_scrubbed

                    content = xml_text.encode("utf-8")

                zout.writestr(item, content)

    summary = {
        "tokens_filled": sorted(set(all_replaced)),
        "tokens_zeroed": sorted(set(all_zeroed)),
        "lines_scrubbed": total_scrubbed,
    }
    return out_buf.getvalue(), summary


# ---------------------------------------------------------------------------
# CLI wrapper — reads/writes files, delegates to fill_template_bytes
# ---------------------------------------------------------------------------

def fill_template(data: dict, output_path: str, template_path: Path = TEMPLATE_VSDX, scrub: bool = True):
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    result_bytes, summary = fill_template_bytes(data, template_path.read_bytes(), scrub=scrub)
    Path(output_path).write_bytes(result_bytes)

    print(f"\n✓ Output written to: {output_path}")
    print(f"  Tokens filled   : {summary['tokens_filled']}")
    if summary["tokens_zeroed"]:
        print(f"  Tokens zeroed   : {summary['tokens_zeroed']}  (missing/empty in JSON)")
    if scrub:
        print(f"  Lines scrubbed  : {summary['lines_scrubbed']}")


def main():
    parser = argparse.ArgumentParser(description="Fill a Visio template with JSON data.")
    parser.add_argument("--data", required=True, help="Path to JSON data file")
    parser.add_argument("--out", required=True, help="Output .vsdx file path")
    parser.add_argument("--template", default=str(TEMPLATE_VSDX), help="Template .vsdx path (optional override)")
    parser.add_argument("--no-scrub", action="store_true",
                        help="Disable empty-line scrubbing (leave blank label lines visible)")
    args = parser.parse_args()

    data = load_data(args.data)
    fill_template(data, args.out, Path(args.template), scrub=not args.no_scrub)


if __name__ == "__main__":
    main()
