// app/page.tsx — one canvas behind, the story in front.
// Each <section data-cue="id"> pins the camera cue with the same id (see engine/product.ts).
import Scene from "./Scene";
import "./scene.css";

export default function Page() {
  return (
    <main className="story-root">
      <Scene verb="power up" />
      <div className="story">
        <section data-cue="hero">
          <h1 data-reveal>Built from code.</h1>
          <p data-reveal>No video files. No downloaded models. Rendered live on your device.</p>
        </section>
        <section data-cue="close">
          <h2 data-reveal>A 0.05 mm edge.</h2>
          <p data-reveal>Every part is real geometry, in real millimetres.</p>
        </section>
        <section data-cue="apart">
          <h2 data-reveal>Take it apart.</h2>
        </section>
        <section data-cue="around" />
        <section data-cue="rebuild">
          <h2 data-reveal>Back together.</h2>
        </section>
        <section data-cue="outro">
          <h2 data-reveal>Yours.</h2>
        </section>
      </div>
    </main>
  );
}
