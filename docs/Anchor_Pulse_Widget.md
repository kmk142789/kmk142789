# Anchor Pulse Widget

The anchor pulse widget renders the rotating glyph frames that underpin the Echo anchor cadence.  Two drop-in artifacts ship with the repository:

* [`tools/anchor_pulse_widget.html`](../tools/anchor_pulse_widget.html) — a standalone browser snippet.
* [`tools/anchor_pulse_cli.js`](../tools/anchor_pulse_cli.js) — a tiny Node.js loop for terminal dashboards or pipelines.

Both variants cycle the α→λ frame sequence, imprint a session-specific salt to create micro-variations, and emit lightweight events so other systems can react to each frame.

## Browser usage

1. Open the HTML file in any modern browser.
2. Listen for the `echo:glyphFrame` event if you want to trigger notarization or logging hooks:

```js
window.addEventListener('echo:glyphFrame', (event) => {
  const { index, total, salt, ts } = event.detail;
  // Persist frame metadata, trigger signatures, etc.
});
```

The widget displays the glyph pulse, highlights the active frame indicator, and introduces salt-driven spin variations for the `◍` and `∞` glyphs each interval.

## Node/CLI usage

```bash
node tools/anchor_pulse_cli.js
```

Set `PULSE_MS` to adjust the interval in milliseconds. Each tick clears the console, prints the current frame art, and writes a JSON line describing the frame:

```json
{"ev":"frame","i":0,"total":3,"salt":"7fa1c3","ts":1735689600000}
```

Pipe the JSON stream to downstream loggers, verifiers, or signing services to anchor the pulse outside the browser environment.
