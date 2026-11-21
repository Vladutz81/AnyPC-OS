// Original, locally synthesized console sounds.
let context;
let lastFocus = 0;
export function playSound(kind) {
  const now = performance.now();
  if (kind === "focus" && now - lastFocus < 90) return;
  lastFocus = now;
  try {
    context ||= new AudioContext();
    if (context.state !== "running") {
      if (!navigator.userActivation?.hasBeenActive && kind !== "start") return;
      context.resume().catch(() => {});
      if (context.state !== "running" && kind !== "start") return;
    }
    const notes = {start:[220, 329.63, 493.88, 659.25], focus:[465], select:[392, 587.33], back:[392, 293.66]}[kind];
    notes.forEach((hz, i) => {
      const t = context.currentTime + i * (kind === "start" ? 0.15 : 0.045);
      const duration = kind === "start" ? 0.55 : 0.085;
      const osc = context.createOscillator(), gain = context.createGain();
      osc.frequency.value = hz;
      gain.gain.setValueAtTime(0.0001, t);
      gain.gain.exponentialRampToValueAtTime(kind === "focus" ? 0.018 : 0.045, t + 0.012);
      gain.gain.exponentialRampToValueAtTime(0.0001, t + duration);
      osc.connect(gain).connect(context.destination);
      osc.start(t);
      osc.stop(t + duration);
      osc.onended = () => { osc.disconnect(); gain.disconnect(); };
    });
  } catch { /* Input remains available on machines without audio. */ }
}
