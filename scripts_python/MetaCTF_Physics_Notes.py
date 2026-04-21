from pathlib import Path


def extract_flag(text: str) -> str:
    lines = [line for line in text.splitlines() if line]
    if len(lines) < 15:
        raise ValueError("expected at least 15 non-empty lines")

    parts = [line[0] + line[-1] for line in lines[:14]]
    parts.append(lines[14][0])
    return "".join(parts)


def main() -> None:
    notes_path = Path("CTF_Writeups/files/Physics Notes/notes.txt")
    text = notes_path.read_text(encoding="utf-8")
    flag = extract_flag(text)
    print(flag)


if __name__ == "__main__":
    main()
