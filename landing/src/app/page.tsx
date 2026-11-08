import Scene from "@/scene/Scene";
import Exterior from "@/sections/Exterior";
import Kitchen from "@/sections/Kitchen";
import Hall from "@/sections/Hall";
import Greenhouse from "@/sections/Greenhouse";
import Workshop from "@/sections/Workshop";
import Launchpad from "@/sections/Launchpad";

export default function Home() {
  return (
    <>
      <Scene />
      <main>
        <Exterior />
        <Kitchen />
        <Hall />
        <Greenhouse />
        <Workshop />
        <Launchpad />
      </main>
    </>
  );
}
