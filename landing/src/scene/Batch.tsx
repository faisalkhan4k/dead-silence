"use client";

import { useLayoutEffect, useRef, type Ref } from "react";
import * as THREE from "three";
import { MATS, type Item, type MatKey } from "./parts";

// One instanced draw call for every box that shares a material.
export default function Batch({
  mat,
  items,
  matRef,
}: {
  mat: MatKey;
  items: Item[];
  matRef?: Ref<THREE.MeshStandardMaterial>;
}) {
  const ref = useRef<THREE.InstancedMesh>(null);
  useLayoutEffect(() => {
    const m = ref.current;
    if (!m) return;
    const o = new THREE.Object3D();
    items.forEach((it, i) => {
      o.position.set(...it.p);
      o.scale.set(...it.s);
      o.updateMatrix();
      m.setMatrixAt(i, o.matrix);
    });
    m.instanceMatrix.needsUpdate = true;
  }, [items]);
  if (!items.length) return null;
  const { emissive, ...spec } = MATS[mat];
  return (
    <instancedMesh ref={ref} args={[undefined, undefined, items.length]} frustumCulled={false}>
      <boxGeometry args={[1, 1, 1]} />
      <meshStandardMaterial ref={matRef} {...spec} emissive={emissive ?? "#000000"} flatShading />
    </instancedMesh>
  );
}
