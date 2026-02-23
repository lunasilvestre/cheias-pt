/**
 * cheias.pt — Temporal player
 *
 * Maps scroll progress (0-1) to animation frames.
 * Used for Chapter 3 (soil moisture) and potentially Chapter 4.
 */

let frames = [];
let currentFrameIndex = -1;
let onFrameChange = null;

export function setFrames(frameArray) {
  frames = frameArray;
  currentFrameIndex = -1;
}

export function setProgress(progress) {
  if (frames.length === 0) return;
  const idx = Math.min(Math.floor(progress * frames.length), frames.length - 1);
  if (idx !== currentFrameIndex && idx >= 0) {
    currentFrameIndex = idx;
    if (onFrameChange) onFrameChange(frames[idx], idx);
  }
}

export function onFrame(callback) {
  onFrameChange = callback;
}

export function getCurrentDate() {
  if (currentFrameIndex < 0 || currentFrameIndex >= frames.length) return '';
  return frames[currentFrameIndex]?.date || '';
}

export function getCurrentFrame() {
  if (currentFrameIndex < 0 || currentFrameIndex >= frames.length) return null;
  return frames[currentFrameIndex];
}

export function getFrameCount() {
  return frames.length;
}

export function reset() {
  frames = [];
  currentFrameIndex = -1;
  onFrameChange = null;
}
