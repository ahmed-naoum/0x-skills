"use client";
// The one fixed canvas behind the page. Copy the engine folder next to this file (./engine).
import { useEffect, useRef, useState } from "react";
import { Engine } from "./engine/Engine";
import { buildProduct, cues } from "./engine/product";
import { Synth, enableTilt, holdTo } from "./engine/pulse";

export default function Scene({ verb = "power up" }: { verb?: string }) {
  const canvas = useRef<HTMLCanvasElement>(null);
  const callouts = useRef<SVGSVGElement>(null);
  const hold = useRef<HTMLButtonElement>(null);
  const [progress, setProgress] = useState(0);
  const [blueprint, setBlueprint] = useState(false);
  const engine = useRef<Engine | null>(null);

  useEffect(() => {
    // The engine owns the canvas for the life of the page. Created in an effect, so it never runs on the server.
    const e = new Engine(canvas.current!, { cues, callouts: callouts.current });
    engine.current = e;
    const synth = new Synth();
    e.pulse.onBeat = () => synth.tick(); // events fire on the beat of the shared clock
    void e.start(buildProduct());

    const release = holdTo(hold.current!, {
      onProgress: setProgress,
      onUnlock: () => {
        synth.unlock(); // browsers gate audio and tilt behind a gesture: one tap unlocks both
        void enableTilt((x, y) => e.setTilt(x, y));
      },
      onComplete: () => synth.thunk(), // replace with the product's verb
    });
    return () => {
      release();
      e.dispose();
      engine.current = null;
    };
  }, []);

  useEffect(() => engine.current?.toggleBlueprint(blueprint), [blueprint]);

  const R = 26, C = 2 * Math.PI * R;
  return (
    <>
      <canvas ref={canvas} className="scene-canvas" aria-hidden="true" />
      <svg ref={callouts} className="scene-callouts" aria-hidden="true" />
      <div className="scene-loader" role="status">Loading</div>
      <div className="scene-controls">
        <button ref={hold} className="hold" aria-label={`Hold to ${verb}`}>
          <svg viewBox="0 0 60 60" width="60" height="60" aria-hidden="true">
            <circle cx="30" cy="30" r={R} fill="none" stroke="currentColor" strokeOpacity=".2" strokeWidth="2" />
            <circle cx="30" cy="30" r={R} fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"
              strokeDasharray={C} strokeDashoffset={C * (1 - progress)} transform="rotate(-90 30 30)" />
          </svg>
          <span>Hold to {verb}</span>
        </button>
        <button className="blueprint" aria-pressed={blueprint} onClick={() => setBlueprint((b) => !b)}>
          Blueprint
        </button>
      </div>
    </>
  );
}
