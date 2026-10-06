# youtube-chat-questions.py
# Author: Jibril Sulaiman
# What: turns a yt-dlp live_chat.json (a YouTube Live chat replay) into two CSVs:
#   every chat message, and just the audience messages that look like questions.
#   Moderator/owner messages are excluded from the questions list, and a viewer
#   pasting the same question more than once counts once.
# Why: capture the questions asked during a YouTube Live without YouTube Data API
#   quota or a Google login. This is the after-the-stream route: yt-dlp downloads
#   the chat replay, this script sorts it.
# How to run (Python 3.8+, standard library only, works offline):
#   python youtube-chat-questions.py "<file>.live_chat.json"
#   Writes <file>.live_chat.all.csv and <file>.live_chat.questions.csv next to it.

import csv
import json
import re
import sys
from pathlib import Path

QUESTION_START = re.compile(
    r"^(how|what|why|when|where|who|which|can|could|should|would|will|is|are|"
    r"do|does|did|was|were|any|anyone|has|have|if)\b",
    re.IGNORECASE,
)

# Moderator and owner messages (e.g. the team's promo lines) are not audience questions.
STAFF_BADGES = {"Moderator", "Owner"}


def run_text(runs):
    parts = []
    for r in runs or []:
        if "text" in r:
            parts.append(r["text"])
        elif "emoji" in r:
            parts.append(r["emoji"].get("shortcuts", [""])[0] if r["emoji"].get("isCustomEmoji") else r["emoji"].get("emojiId", ""))
    return "".join(parts).strip()


def looks_like_question(text):
    t = text.strip()
    if len(t) < 8:
        return False
    if "?" in t:
        return True
    return bool(QUESTION_START.match(t)) and len(t.split()) >= 4


def main(src):
    src = Path(src)
    rows = []
    for line in src.open(encoding="utf-8"):
        d = json.loads(line)
        replay = d.get("replayChatItemAction", {})
        offset_ms = int(replay.get("videoOffsetTimeMsec", 0) or 0)
        for action in replay.get("actions", []):
            item = action.get("addChatItemAction", {}).get("item", {})
            r = item.get("liveChatTextMessageRenderer") or item.get("liveChatPaidMessageRenderer")
            if not r:
                continue
            text = run_text(r.get("message", {}).get("runs"))
            if not text:
                continue
            badges = {b.get("liveChatAuthorBadgeRenderer", {}).get("tooltip", "") for b in r.get("authorBadges", [])}
            is_staff = bool(badges & STAFF_BADGES)
            secs = offset_ms // 1000
            rows.append({
                "stream_time": f"{secs // 3600}:{secs % 3600 // 60:02d}:{secs % 60:02d}",
                "offset_seconds": secs,
                "author": r.get("authorName", {}).get("simpleText", ""),
                "channel_id": r.get("authorExternalChannelId", ""),
                "message": text,
                "is_staff": is_staff,
                "is_question": looks_like_question(text) and not is_staff,
                "message_id": r.get("id", ""),
            })

    # Same viewer pasting the same question repeatedly counts once.
    seen = set()
    for x in rows:
        key = (x["channel_id"], x["message"].lower())
        if x["is_question"] and key in seen:
            x["is_question"] = False
        seen.add(key)

    base = src.with_suffix("")  # strip .json
    fields = list(rows[0].keys()) if rows else []
    for path, subset in ((f"{base}.all.csv", rows), (f"{base}.questions.csv", [x for x in rows if x["is_question"]])):
        with open(path, "w", newline="", encoding="utf-8-sig") as fh:
            w = csv.DictWriter(fh, fieldnames=fields)
            w.writeheader()
            w.writerows(subset)
        print(f"{len(subset):>6} rows -> {path}")


if __name__ == "__main__":
    main(sys.argv[1])
