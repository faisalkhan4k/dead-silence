import Scene from "@/scene/Scene";
import Hull from "@/sections/Hull";
import Comms from "@/sections/Comms";
import Corridor from "@/sections/Corridor";
import Reactor from "@/sections/Reactor";
import Cargo from "@/sections/Cargo";
import Airlock from "@/sections/Airlock";

export default function Home() {
  return (
    <>
      <Scene />
      <main>
        <Hull />
        <Comms />
        <Corridor />
        <Reactor />
        <Cargo />
        <Airlock />
      </main>
    </>
  );
}
