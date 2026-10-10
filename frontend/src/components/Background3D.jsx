import React, { useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { MeshDistortMaterial, Float } from '@react-three/drei';
import * as THREE from 'three';

function MorphingSphere({ isDark }) {
  const mainMeshRef = useRef();
  const twinMeshRef = useRef();
  
  // Smoothly interpolate color
  const targetColor = new THREE.Color(isDark ? '#6366f1' : '#dcbfa8'); // Bright indigo for dark, warm latte for light
  
  useFrame((state, delta) => {
    if (mainMeshRef.current && twinMeshRef.current) {
      mainMeshRef.current.material.color.lerp(targetColor, 3 * delta);
      twinMeshRef.current.material.color.lerp(targetColor, 3 * delta);
      
      // Give the twin a slightly different rotation speed
      twinMeshRef.current.rotation.y += delta * 0.1;
      twinMeshRef.current.rotation.x += delta * 0.05;
    }
  });

  return (
    <>
      <Float speed={1.5} rotationIntensity={0.5} floatIntensity={1}>
        <mesh ref={mainMeshRef} scale={2.2} position={[0, 0, -1]}>
          <sphereGeometry args={[1, 64, 64]} />
          <MeshDistortMaterial
            attach="material"
            distort={0.4} 
            speed={1.5} 
            roughness={0.3}
            metalness={0.1}
          />
        </mesh>
      </Float>
      
      {/* Distant Twin Sphere */}
      <Float speed={0.8} rotationIntensity={1} floatIntensity={0.5}>
        <mesh ref={twinMeshRef} scale={0.8} position={[3, 2, -5]}>
          <sphereGeometry args={[1, 64, 64]} />
          <MeshDistortMaterial
            attach="material"
            distort={0.6} 
            speed={1.0} 
            roughness={0.4}
            metalness={0.2}
            opacity={0.7}
            transparent={true}
          />
        </mesh>
      </Float>
    </>
  );
}

export default function Background3D({ isDark }) {
  return (
    <div className="fixed inset-0 z-[-1] pointer-events-none transition-opacity duration-1000 opacity-50 dark:opacity-40">
      <Canvas camera={{ position: [0, 0, 5], fov: 45 }}>
        <ambientLight intensity={isDark ? 0.8 : 1.2} />
        <directionalLight 
          position={[5, 5, 5]} 
          intensity={isDark ? 1.5 : 2} 
          color={isDark ? '#818cf8' : '#ffffff'} 
        />
        <pointLight 
          position={[-5, -5, 2]} 
          intensity={isDark ? 2 : 1} 
          color={isDark ? '#4338ca' : '#ffedd5'} 
        />
        <MorphingSphere isDark={isDark} />
      </Canvas>
    </div>
  );
}
