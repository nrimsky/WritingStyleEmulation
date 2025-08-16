"""
Step 1: Generate a description of an author's style from their texts to use as a system prompt.
Step 2: Backtranslate texts to generate prompts that could have been used to write them.
Step 3: Generate a conversation history with the backtranslated prompts and the original texts.
Step 4: Use the conversation history, alongside the description from step 1 as a system prompt, to generate a new text.

Usage:
python pipeline.py
"""

from glob import glob
import os
from typing import NamedTuple
from datetime import datetime
from tqdm import tqdm
import json
from api import Message, sample

LOGS_DIR = "logs"

DESCRIBE_SYSTEM = "The Assistant analyzes texts provided by the User. All the texts are written by the same author. The Assistant produces a detailed bullet-point list of distinctive qualities of the author's style. The focus is not on the content of the texts, but on the stylistic elements such as tone, vocabulary, and sentence structure."

DESCRIBE_PROMPT = """Here is a collection of texts written by the same author. Please analyze these texts and generate a detailed bullet-point list of distinctive qualities of the author's style. Return the bullet points in <bullet_points></bullet_points> tags.

<texts>
{texts}
</texts>"""

BACKTRANSLATE_SYSTEM = "The Assistant generates concise prompts that capture the essence of a piece of writing provided by the User. The resultant prompt can be used by another author to write a similar piece."

BACKTRANSLATE_PROMPT = """I have provided a piece of writing below (in <content></content> tags).
Please generate a short prompt that could be used by another author to write a similar piece.
The prompt should be concise and capture the essence of the original text.
Return your prompt in <prompt></prompt> tags.

<content>
{content}
</content>"""

File = NamedTuple("File", [("path", str), ("content", str)])


def glob_and_read_files(user_ordering: bool = False) -> list[File]:
    glob_path = input("Enter the glob path to the texts (e.g., 'texts/*.md'): ").strip()
    paths = glob(glob_path)
    if not paths:
        raise ValueError(f"No files found for glob path: {glob_path}")

    if user_ordering:
        filenames = [os.path.basename(path) for path in paths]
        print(
            "Please select an ordering for the files (enter ordering separated by commas):"
        )
        for i, filename in enumerate(filenames):
            print(f"{i + 1}) {filename}")
        ordering = input("Ordering: ").strip().split(",")
        ordering = [int(x.strip()) - 1 for x in ordering if x.strip().isdigit()]
        ordered_paths = [paths[i] for i in ordering if 0 <= i < len(paths)]
        if not ordered_paths:
            raise ValueError("No valid files selected based on the ordering.")
    else:
        ordered_paths = sorted(paths)

    files = []
    for path in ordered_paths:
        with open(path, "r") as f:
            content = f.read().strip()
        files.append(File(path=path, content=content))
    return files


def main():
    full_logs_dir = os.path.join(LOGS_DIR, datetime.now().isoformat())
    os.makedirs(full_logs_dir, exist_ok=True)

    print("Step 1: Generate a description of the author's style.")
    print("Provide a glob file to the texts to analyze for the system prompt.")
    files = glob_and_read_files(user_ordering=False)
    describe_prompt = DESCRIBE_PROMPT.format(
        texts="\n".join(f"<text>\n{file.content}\n</text>" for file in files)
    )
    result = sample(
        messages=[{"role": "user", "content": describe_prompt}],
        system_prompt=DESCRIBE_SYSTEM,
        max_tokens=7000,
    )
    system_prompt = (
        result.split("<bullet_points>")[1].split("</bullet_points>")[0].strip()
    )
    with open(os.path.join(full_logs_dir, "system_prompt.txt"), "w") as f:
        f.write(system_prompt)

    print("Step 2: Backtranslate the texts to generate prompts.")
    print(
        "Provide a glob file to the texts to backtranslate (you will be able to subselect and reorder them)."
    )
    backtranslate_files = glob_and_read_files(user_ordering=True)
    conversation_history: list[Message] = []
    for file in tqdm(backtranslate_files):
        backtranslate_prompt = BACKTRANSLATE_PROMPT.format(content=file.content)
        response = sample(
            messages=[{"role": "user", "content": backtranslate_prompt}],
            system_prompt=BACKTRANSLATE_SYSTEM,
            max_tokens=7000,
        )
        prompt = response.split("<prompt>")[1].split("</prompt>")[0].strip()
        conversation_history.append({"role": "user", "content": prompt})
        conversation_history.append({"role": "assistant", "content": file.content})
    with open(
        os.path.join(full_logs_dir, "backtranslated_conversation.json"), "w"
    ) as f:
        json.dump(conversation_history, f)

    print(
        "Step 3: Generate a new piece using the backtranslated prompts, original content, and generated system prompt."
    )
    final_prompt = input(
        "Enter a final prompt for the generation of the new piece (if you provide a .txt path, it'll be read): "
    ).strip()
    if final_prompt.endswith(".txt"):
        with open(final_prompt, "r") as f:
            final_prompt = f.read().strip()
    conversation_history.append({"role": "user", "content": final_prompt})
    with open(os.path.join(full_logs_dir, "final_full_prompt.json"), "w") as f:
        json.dump(
            {
                "system_prompt": system_prompt,
                "messages": conversation_history,
            },
            f,
        )
    response = sample(
        messages=conversation_history,
        system_prompt=system_prompt,
        max_tokens=7000,
    )
    output_path = os.path.join(full_logs_dir, "generated_piece.md")
    with open(output_path, "w") as f:
        f.write(response)
    print(f"Generated piece saved to {output_path}")
    print("Pipeline completed successfully.")


if __name__ == "__main__":
    main()
