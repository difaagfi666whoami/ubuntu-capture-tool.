# Product Requirements Document

## Summary
An Ubuntu-only desktop utility for repetitive area screenshots and simple image composition. Product name: Dipapipi Skrinsyun kustom.

## User problems
- Repeated screenshots require resizing the selection every time.
- Combining screenshots should not require opening GIMP.

## Goals
- Reuse previous selection dimensions on supported environments.
- Combine multiple screenshots vertically or horizontally.
- Keep installation and use simple.
- Publish a credible, documented GitHub repository.

## MVP scope: area capture
1. Invoke area capture.
2. Show the previous selection dimensions as the initial rectangle when backend supports it.
3. Allow moving/resizing before capture where supported.
4. Save capture using a unique filename.
5. Persist last geometry between app launches.

Persist width/height. Persist x/y only when valid. Recover from out-of-bounds geometry. Cancel must not create a file. Never silently overwrite.

## MVP scope: image combiner
1. Select 2+ images.
2. Reorder images.
3. Choose Vertical or Horizontal.
4. Choose alignment for different dimensions: Start, Center, End.
5. Preview and export a PNG by default.

Preserve aspect ratio. Source files are read-only. Invalid files and unwritable output paths must produce useful errors. Do not silently overwrite output.

## Non-goals
Screen recording, OCR, annotation tools, cloud sync, accounts, telemetry, uploads, scrolling capture, advanced retouching, Windows/macOS support.

## Success criteria
- Repeated capture avoids manually resizing the selection on a tested supported environment.
- Images can be combined in either direction without an external editor.
- README install instructions work on the declared Ubuntu environment.
- Compatibility claims are backed by manual test evidence.

## Open questions
Ubuntu version, desktop environment, display server, capture backend, global hotkey support, and default output folder.
