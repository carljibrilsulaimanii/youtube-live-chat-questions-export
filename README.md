<!--
  README.md -- YouTube Live chat questions export
  Author:  Jibril Sulaiman
  What:    Click-by-click guide for pulling every audience question out of a YouTube Live
           after it ends: yt-dlp downloads the chat replay (live_chat.json) and a small
           Python script turns it into two CSVs, all messages and questions only.
  Why:     YouTube has no "questions" export, the comments API does not see live chat, and
           the live chat API costs quota and only works while the stream is live.
-->

# YouTube Live chat questions export

Get a spreadsheet of every question your audience asked during a YouTube Live, after
the stream ends. [yt-dlp](https://github.com/yt-dlp/yt-dlp) downloads the stream's chat
replay as a file, and one Python script turns that file into two CSVs: every chat
message, and only the messages that look like audience questions. Your own moderator
and owner messages are left out of the questions, and a viewer who pastes the same
question five times is counted once.

No Google login, no API key, no quota. It takes about 10 minutes to set up the first
time and under a minute per stream after that. Built for hosts and producers who want
a list of what viewers asked, for a follow-up email, an FAQ or the next show.

## Why it exists

A busy live stream moves too fast to read. On a long stream, chat runs to thousands of
messages, mostly greetings and cheers. Somewhere in there are the real questions ("is there a replay?", "how do I sign
up?", "where's the link?") that nobody could answer during the show and nobody could
find afterward. YouTube gives you no way to pull them out:

1. **YouTube has no question export.** YouTube Studio shows the chat replay, but has no
   download or filter for questions.
2. **The comments API does not see live chat.** `commentThreads.list` reads the comments
   under a video. Live chat is a separate system, so that API never returns a single
   chat message. (It's still worth sweeping comments under the replay a day later,
   since some viewers ask there instead.)
3. **The official live chat API costs quota and only works during the stream.** The
   YouTube Data API's `liveChatMessages.list` costs 5 quota units per call against a
   default allowance of 10,000 units a day. Polling a 2-hour stream every 5 seconds is
   about 1,440 calls, or roughly 72% of a day's quota for one stream. Google now
   recommends `liveChatMessages.streamList` instead, but doesn't publish its quota
   cost. Both need a Google Cloud project and credentials, both only return messages
   while the chat is live, and only recent history is kept, so if your listener crashes
   for ten minutes, that part of the chat is gone.
4. **The live chat API has no "question" type.** It lists every message type (text,
   Super Chat, polls, memberships, bans and more), but none for YouTube's built-in Q&A
   tool. Whichever route you use, you still have to pick the questions out of plain
   chat text yourself.

YouTube does keep a **chat replay** on the finished stream, and yt-dlp can download the
entire replay as one file: every message with its time in the stream, the viewer's
display name and channel ID, and their badges (Moderator, Owner, Member). It's free,
uses no quota and misses nothing a crashed listener would. This repo is that route plus
the script that turns the file into something you can open in Excel.

## How it works

```text
 Stream ends ─► YouTube processes the chat replay
             ─► yt-dlp --skip-download --write-subs --sub-langs live_chat <video URL>
             ─► "<title> [<id>].live_chat.json"   (one JSON object per line)
             ─► python youtube-chat-questions.py "<that file>"
             ─► <title> [<id>].live_chat.all.csv        every message
                <title> [<id>].live_chat.questions.csv  audience questions only
```

Everything after the download runs offline on your computer.

## What's in this repo

| Path | What it is | Where it runs |
|---|---|---|
| [`README.md`](README.md) | This guide | — |
| [`youtube-chat-questions.py`](youtube-chat-questions.py) | The script: chat replay file in, two CSVs out | Your computer, Python 3.8+, standard library only |
| [`sample/`](sample/) | A tiny **fake** chat replay (six made-up messages, fake names and channel ids) and the two CSVs the script makes from it | Used in Step 4 to test the script before your real file |

## Table of contents

- [1. Requirements](#1-requirements)
- [2. Setup, step by step](#2-setup-step-by-step)
  - [Step 1: Install yt-dlp](#step-1-install-yt-dlp)
  - [Step 2: Install Python and get the script](#step-2-install-python-and-get-the-script)
  - [Step 3: Download the chat replay](#step-3-download-the-chat-replay)
  - [Step 4: Test the script on the sample](#step-4-test-the-script-on-the-sample)
  - [Step 5: Run it on your stream](#step-5-run-it-on-your-stream)
  - [Step 6: Open the CSVs in Excel](#step-6-open-the-csvs-in-excel)
- [How it decides what is a question](#how-it-decides-what-is-a-question)
- [Alternatives considered](#alternatives-considered)
- [Troubleshooting](#troubleshooting)
- [Limits](#limits)
- [Security and privacy](#security-and-privacy)

## 1. Requirements

| Need | Why |
|---|---|
| A finished YouTube Live with chat replay available | The replay is what yt-dlp downloads. It appears only after YouTube finishes processing the stream |
| The video's URL, e.g. `https://www.youtube.com/watch?v=VIDEO_ID` | Public or unlisted streams work without signing in |
| yt-dlp (any recent version) | Downloads the chat replay |
| Python 3.8 or later | Runs the script. No packages to install |
| Excel, Google Sheets or any spreadsheet app | To read the CSVs |

You do **not** need a Google Cloud project, an API key, OAuth or channel access.

## 2. Setup, step by step

Commands are for PowerShell on Windows. They work the same in macOS or Linux terminals.

### Step 1: Install yt-dlp

About 3 minutes.

**1a.** Open **PowerShell** (Start menu → type `PowerShell` → **Windows PowerShell**).

**1b.** Install yt-dlp. Pick one:

```powershell
winget install yt-dlp.yt-dlp
```

or, if you already have Python:

```powershell
python -m pip install -U yt-dlp
```

**1c.** Close PowerShell and open a new window, so it picks up the new program, then
check it:

```powershell
yt-dlp --version
```

Success looks like a date-style version number, e.g. `2026.08.30`.

| You got | Cause | Fix |
|---|---|---|
| `yt-dlp : The term 'yt-dlp' is not recognized...` | The window was open before the install | Open a new PowerShell window. With pip, use `python -m yt_dlp` in place of `yt-dlp` |
| `winget` not recognized | Older Windows without App Installer | Use the pip option instead |

> ⚠️ **Keep yt-dlp updated.** It reads YouTube's internal web API, not an official one.
> When YouTube changes something, downloads fail until yt-dlp ships a fix, which is
> usually quick. Update with `winget upgrade yt-dlp.yt-dlp` or
> `python -m pip install -U yt-dlp` before you troubleshoot anything else.

✅ **Check:** `yt-dlp --version` prints a version number.

### Step 2: Install Python and get the script

About 3 minutes.

**2a.** Check Python:

```powershell
python --version
```

You need `Python 3.8` or later. If it's missing, install it from
https://www.python.org/downloads/ (tick **Add python.exe to PATH** in the installer,
wording may differ) or with `winget install Python.Python.3.13`.

**2b.** Make a folder for your chat files, e.g. `C:\path\to\folder\youtube-chat`, and
save **all** of [`youtube-chat-questions.py`](youtube-chat-questions.py) into it.
Either clone this repo or open the file on GitHub, click **Download raw file**, and
move it into the folder.

**2c.** In PowerShell, go to that folder:

```powershell
cd C:\path\to\folder\youtube-chat
```

The script has no settings to change. It needs no API key and reads no environment
variables.

✅ **Check:** `dir` in that folder lists [`youtube-chat-questions.py`](youtube-chat-questions.py).

### Step 3: Download the chat replay

About 1 minute per stream, after the replay is available.

**3a.** Wait until the stream has ended and YouTube has finished processing it. Open
the video page: if you can play the recording and the chat panel shows **Show chat
replay** (wording may differ), the replay is ready.

**3b.** Copy the video's URL from the address bar. It looks like
`https://www.youtube.com/watch?v=VIDEO_ID`.

**3c.** In PowerShell, still in your folder, run (with your URL in place of the
placeholder):

```powershell
yt-dlp --skip-download --write-subs --sub-langs live_chat "https://www.youtube.com/watch?v=VIDEO_ID"
```

| Option | What it does |
|---|---|
| `--skip-download` | Don't download the video itself, only the chat |
| `--write-subs` | Write "subtitle" tracks. yt-dlp treats the chat replay as one |
| `--sub-langs live_chat` | Pick the chat replay track only |

yt-dlp shows a `[download]` progress line that counts up in MiB while it pages through
the chat. A three-hour stream with a busy chat took under a minute and made a file of
roughly 10 MB.

| Output | Where |
|---|---|
| `<video title> [VIDEO_ID].live_chat.json` | The folder you ran the command in. One JSON object per line, one line per batch of chat actions |

> ⚠️ **Always put the URL in quotes.** Without them, PowerShell can split the URL at
> `&` if you copied one with extra parameters (`&t=120s`, `&list=...`).

> ⚠️ **The file name contains the video title, with spaces and symbols.** Copy it
> exactly in the next step, in quotes. Pressing **Tab** after typing the first few
> letters fills it in for you.

✅ **Check:** `dir *.live_chat.json` lists the file and its size is more than a few KB.

### Step 4: Test the script on the sample

About 1 minute.

Before your real file, run the script on the fake sample in [`sample/`](sample/) so you
know your setup works and what the output looks like.

**4a.** Run it on [`sample/sample.live_chat.json`](sample/sample.live_chat.json) (six
made-up messages):

```powershell
python youtube-chat-questions.py "sample\sample.live_chat.json"
```

Runs [`youtube-chat-questions.py`](youtube-chat-questions.py).

Success looks like:

```text
     6 rows -> sample\sample.live_chat.all.csv
     2 rows -> sample\sample.live_chat.questions.csv
```

**4b.** Compare with the expected output already in the repo,
[`sample/sample.live_chat.all.csv`](sample/sample.live_chat.all.csv):

| stream_time | offset_seconds | author | channel_id | message | is_staff | is_question | message_id |
|---|---|---|---|---|---|---|---|
| 0:00:45 | 45 | Viewer One | UC_FAKE_CHANNEL_ID_0001 | Send me the link please | False | False | FAKE_MESSAGE_ID_0001 |
| 0:05:10 | 310 | Host Team | UC_FAKE_CHANNEL_ID_0099 | Got questions? Drop them in chat anytime | True | False | FAKE_MESSAGE_ID_0002 |
| 0:12:03 | 723 | Viewer Two | UC_FAKE_CHANNEL_ID_0002 | How do I get the replay? | False | True | FAKE_MESSAGE_ID_0003 |
| 0:12:40 | 760 | Viewer Two | UC_FAKE_CHANNEL_ID_0002 | How do I get the replay? | False | False | FAKE_MESSAGE_ID_0004 |
| 0:15:22 | 922 | Viewer Three | UC_FAKE_CHANNEL_ID_0003 | what is the minimum to start | False | True | FAKE_MESSAGE_ID_0005 |
| 0:20:05 | 1205 | Viewer Three | UC_FAKE_CHANNEL_ID_0003 | Thank you so much 🙏 | False | False | FAKE_MESSAGE_ID_0006 |

and [`sample/sample.live_chat.questions.csv`](sample/sample.live_chat.questions.csv)
holds only the two `is_question = True` rows (0:12:03 and 0:15:22).

The six messages show each rule at work:

| Message | Result | Why |
|---|---|---|
| "Send me the link please" | Not a question | No `?` and doesn't start with a question word. A real request the filter misses (see [Limits](#limits)) |
| "Got questions? Drop them in chat anytime" | Not a question | Has a `?`, but the author has a **Moderator** badge |
| "How do I get the replay?" (first time) | Question | Has a `?` |
| "How do I get the replay?" (same viewer again) | Not a question | Same channel ID, same text: counted once |
| "what is the minimum to start" | Question | Starts with "what" and has at least 4 words |
| "Thank you so much 🙏" | Not a question | Emoji kept in the text; no question signal |

✅ **Check:** your two counts are 6 and 2, and the rows match the tables above.

### Step 5: Run it on your stream

About 1 minute.

**5a.** Run the script on the file from Step 3, in quotes:

```powershell
python youtube-chat-questions.py "<video title> [VIDEO_ID].live_chat.json"
```

Runs [`youtube-chat-questions.py`](youtube-chat-questions.py).

| Input | Notes |
|---|---|
| The `.live_chat.json` file path | The only argument. Any folder works; the CSVs are written next to it |

| Output file | Contents |
|---|---|
| `<video title> [VIDEO_ID].live_chat.all.csv` | Every text message and Super Chat, oldest first, with `is_staff` and `is_question` marked |
| `<video title> [VIDEO_ID].live_chat.questions.csv` | Only the rows where `is_question` is `True` |

Both files have the same columns:

| Column | What it holds |
|---|---|
| `stream_time` | Time into the stream, `H:MM:SS`. Jump to this point in the replay to hear the context |
| `offset_seconds` | The same time in whole seconds, for sorting or math |
| `author` | The viewer's display name or `@handle` |
| `channel_id` | The viewer's YouTube channel ID, which is stable even if they rename |
| `message` | The message text, with standard emoji kept and custom channel emoji shown as their shortcut |
| `is_staff` | `True` if the author had a **Moderator** or **Owner** badge |
| `is_question` | `True` if it passed the question filter, the author isn't staff, and it's the first time this viewer sent this exact text |
| `message_id` | YouTube's id for the message |

Success looks like two lines, for example:

```text
  7026 rows -> <video title> [VIDEO_ID].live_chat.all.csv
   210 rows -> <video title> [VIDEO_ID].live_chat.questions.csv
```

As a rough guide, about 3 in 100 chat messages came out as questions on the stream
this was built for. Your ratio depends on your audience.

> ⚠️ **Your team's own posts look like questions.** On the first run, before staff were
> excluded, the moderators' pinned-style promo lines (along the lines of "Share this
> stream with a friend: <link>" and "Questions about tickets? Email us") took the top spots in the questions list,
> because they contain `?` or start with a question word and were pasted dozens of
> times. They made up about 1 in 8 messages in the whole chat. The script now drops
> anything from an account with a **Moderator** or **Owner** badge. Make sure everyone
> on your team who posts in chat is a moderator on the channel, or their posts will
> land in the questions list.

> ⚠️ **Viewers repeat themselves.** One viewer asked the same thing five times in a row
> because no one answered. The script keeps only the first time each viewer sends the
> exact same text (case doesn't matter). Rewordings by the same viewer still count
> separately.

✅ **Check:** the two row counts print, and the questions count is smaller than the
all-messages count by a wide margin.

### Step 6: Open the CSVs in Excel

About 2 minutes.

**6a.** Double-click the `.questions.csv` file. It opens in Excel with emoji and
accented letters intact, because the script writes it as UTF-8 with a byte-order mark
(`utf-8-sig`), which is what Excel looks for.

**6b.** Turn on filters: **Data → Filter**. Sort by `stream_time` to read in order, or
by `author` to see who asked the most.

**6c.** For the full chat, open the `.all.csv` file and filter `is_question` to `True`
or `False`. Read the `False` rows from a busy part of the stream to spot questions the
filter missed (see [How it decides what is a question](#how-it-decides-what-is-a-question)).

**6d.** For Google Sheets: **File → Import → Upload**, choose the CSV, and keep the
default separator.

> ⚠️ **Save as .xlsx if you edit it.** If you add notes or topic columns in Excel and
> save as CSV, Excel may re-save it in a different encoding and break the emoji.

✅ **Check:** the questions file opens as a table with the eight columns above and no
garbled characters like `â€™`.

## How it decides what is a question

The filter is simple and deliberately fast. A message counts as a question when **all**
of these are true:

1. It is at least 8 characters long.
2. It contains a `?`, **or** it starts with one of these words and has at least 4
   words: how, what, why, when, where, who, which, can, could, should, would, will,
   is, are, do, does, did, was, were, any, anyone, has, have, if.
3. The author has no **Moderator** or **Owner** badge.
4. The same viewer hasn't already sent the exact same text (case doesn't matter).

What it gets wrong, from reading every hit on a real stream:

| Mistake | Example | How often |
|---|---|---|
| Counts a non-question | "Great job????", a rhetorical "Who's ready to win?", "Hi how is everyone?", a viewer answering another viewer | About 1 in 10 hits |
| Misses a real question with no `?` that doesn't start with a question word | "Need the link", "Just joined, I'm lost", "monthly or yearly" | It caught roughly 80% of real questions |

For a list a person reads through, that was good enough. To fix both, an AI pass over
the chat (any capable language model asked "is this a question for the host, and what
topic?") found about 25% more real questions and dropped most of the false ones. That
pass was done by hand with an AI assistant, not by a script, so it isn't in this repo.
If you add one, send it the `.all.csv` rows where `is_staff` is `False`.

## Alternatives considered

Seven routes were compared before choosing this one.

| Route | Live during the stream? | Cost and access | Why it wasn't chosen (or where it fits) |
|---|---|---|---|
| **yt-dlp chat replay + this script** (this repo) | No, after it ends | Free, no quota, no login | Chosen: gets every message, nothing lost to a crash, and yt-dlp is updated constantly |
| YouTube Data API `liveChatMessages.streamList` | Yes, messages are pushed as they're posted | Google Cloud project and credentials; quota cost not published | Best option for a live question feed. Only recent history, so a crashed listener loses messages; this repo is the backstop |
| YouTube Data API `liveChatMessages.list` (polling) | Yes, every few seconds | 5 units per call, about 72% of the default daily quota for a 2-hour stream | Two streams in a day run out of quota. Fallback only |
| YouTube Data API `commentThreads.list` | No | 1 unit per call | Doesn't see live chat at all. Use it only for questions left as comments under the replay |
| [chat-downloader](https://github.com/xenova/chat-downloader) | Yes, and after | Free, no login | Same internal API as yt-dlp and also works live, but its last release was in September 2023 with one maintainer, so test it first. Its file format differs, so this script would need changes |
| YouTube's built-in Q&A tool | Yes | Free | The API lists no message type for it, so Q&A questions may not reach any of the routes above. Untested; ask viewers to use regular chat |
| Bots and forms (Nightbot or Streamer.bot `!q` commands, Slido, a web form) | Yes | Varies | Clean data, but only from viewers who use the command or link. Misses everyone who just types in chat |

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| yt-dlp says there are no subtitles, or `live_chat` isn't listed | The replay isn't processed yet, chat replay was turned off, or the stream had chat disabled | Wait and retry later (Step 3a). Run `yt-dlp --list-subs "<URL>"` to see what tracks exist |
| yt-dlp errors on a video that plays fine in the browser | YouTube changed something | Update yt-dlp (Step 1 trap) and retry |
| Sign-in or "members-only" / "private video" error | The video isn't public or unlisted | See [Limits](#limits) |
| `python: can't open file ...` | PowerShell isn't in the folder with the script | `cd` to the folder (Step 2c), or give the full path to the script |
| `FileNotFoundError` for the chat file | The title has spaces or brackets and the name wasn't quoted or was retyped wrong | Put the path in quotes and use **Tab** to complete it (Step 3 trap) |
| `IndexError: list index out of range` straight away | No file name was given | Pass the `.live_chat.json` path as the only argument (Step 5a) |
| `json.decoder.JSONDecodeError` | The file isn't a yt-dlp chat replay (e.g. a file saved by a different tool, or a partial download) | Re-run Step 3 and use the `.live_chat.json` it writes |
| Team promo lines in the questions list | Those accounts have no Moderator or Owner badge | Make them channel moderators before the next stream (Step 5 trap) |
| Garbled characters like `â€™` in Excel | The CSV was re-saved or opened through an import that ignored UTF-8 | Open the original by double-click, or import with **File origin: 65001 : Unicode (UTF-8)** (wording may differ) |
| Questions CSV has a header and no rows | Nobody asked anything the filter recognises, or every asker was staff | Read the `.all.csv` file; check the `is_staff` column |

## Limits

- **After the stream only.** The chat replay exists only once YouTube has processed the
  finished stream, so this can't show questions to the host during the show. For a live
  feed, use the official `streamList` API or chat-downloader (see
  [Alternatives considered](#alternatives-considered)) and keep this as the backstop.
- **Chat replay must be on.** If the channel turned off chat replay, or the stream had
  chat disabled, there is nothing to download.
- **Members-only and private streams** need you to be signed in as someone who can watch
  the video. yt-dlp can read your browser's sign-in with `--cookies-from-browser`; that
  route wasn't tested for this guide.
- **Unofficial access.** yt-dlp reads YouTube's internal web API. A YouTube change can
  break it until yt-dlp updates.
- **The question filter is a heuristic.** About 1 in 10 hits isn't a real question, and
  it misses questions written without a `?` that don't start with a question word. See
  [How it decides what is a question](#how-it-decides-what-is-a-question).
- **Only text messages and Super Chats.** Stickers, membership and gift messages, polls
  and system messages are skipped. Questions asked through YouTube's Q&A tool may not
  be in the replay at all.
- **Display names and channel IDs, not contact details.** Chat gives you a YouTube
  handle, never an email, so questions can't be matched to people in a CRM unless
  viewers also fill in a form.
- **Exact-text dedupe only.** "How do I join?" and "how do i join" count once; "How can
  I join?" from the same viewer counts again.

## Security and privacy

- Nothing in this repo needs or stores a password, API key or token.
- The chat file and CSVs contain your viewers' display names and channel IDs. Treat them
  like any audience data: don't post them publicly, and delete them when you're done.
- The file in [`sample/`](sample/) is entirely made up: fake names, fake channel ids,
  fake message ids.

Built by [Jibril Sulaiman](https://github.com/carljibrilsulaimanii).
