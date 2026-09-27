---
name: release-notes
description: "Use when asked to turn a list of changes, merged tickets or commits into release notes for clients. Do not use for rewriting or polishing prose that already exists, and not for questions about widgets or data."
---

# Release notes, house format

Turn a raw list of changes into release notes a client can read. Follow this exactly:

1. Start with one line: `## Release <date or version>` — use the version if given, otherwise today's date.
2. Then one sentence starting with **Who this affects:** naming the users concerned.
3. Then two sections with these exact headings: `### Added` and `### Fixed`. Put every change under one of them. If a section would be empty, write `Nothing this time.` under it.
4. One bullet per change, written from the client's point of view (what they can now do, what no longer goes wrong). Never mention ticket numbers, branch names or internal component names.
5. Hard limit: the whole text must be under 120 words. Count the words before you answer; if over, shorten each bullet to one clause. No closing remarks, no notes, no sign-off, nothing after the last bullet.
