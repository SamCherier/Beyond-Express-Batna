import React, { useRef, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import * as THREE from 'three';

// Algerian Wilayas coordinates (simplified for visualization)
const ALGERIA_POINTS = [
  { name: 'Alger', lat: 36.7538, lon: 3.0588, size: 1.5 },
  { name: 'Oran', lat: 35.6969, lon: -0.6331, size: 1.2 },
  { name: 'Constantine', lat: 36.3650, lon: 6.6147, size: 1.0 },
  { name: 'Batna', lat: 35.5559, lon: 6.1741, size: 0.8 },
  { name: 'Sétif', lat: 36.1905, lon: 5.4106, size: 0.8 },
  { name: 'Annaba', lat: 36.9000, lon: 7.7667, size: 0.8 },
  { name: 'Blida', lat: 36.4703, lon: 2.8277, size: 0.7 },
  { name: 'Tlemcen', lat: 34.8780, lon: -1.3150, size: 0.7 },
  { name: 'Béjaïa', lat: 36.7525, lon: 5.0556, size: 0.7 },
  { name: 'Biskra', lat: 34.8481, lon: 5.7245, size: 0.7 },
];

// Convert lat/lon to 3D coordinates (simplified projection)
const latLonToVector3 = (lat, lon, radius = 5) => {
  const phi = (90 - lat) * (Math.PI / 180);
  const theta = (lon + 180) * (Math.PI / 180);
  
  const x = -(radius * Math.sin(phi) * Math.cos(theta));
  const z = radius * Math.sin(phi) * Math.sin(theta);
  const y = radius * Math.cos(phi);
  
  return new THREE.Vector3(x, y, z);
};

// Particle system for network effect
function ParticleNetwork() {
  const particles = useRef();
  const lines = useRef();
  
  const particlesData = useMemo(() => {
    const positions = [];
    const colors = [];
    
    ALGERIA_POINTS.forEach((point) => {
      const pos = latLonToVector3(point.lat, point.lon);
      positions.push(pos.x, pos.y, pos.z);
      colors.push(1, 0.2, 0.2); // Red glow
    });
    
    return { positions: new Float32Array(positions), colors: new Float32Array(colors) };
  }, []);
  
  const linesData = useMemo(() => {
    const positions = [];
    const colors = [];
    
    // Create connections between cities
    for (let i = 0; i < ALGERIA_POINTS.length; i++) {
      for (let j = i + 1; j < ALGERIA_POINTS.length; j++) {
        if (Math.random() > 0.6) { // 40% chance of connection
          const pos1 = latLonToVector3(ALGERIA_POINTS[i].lat, ALGERIA_POINTS[i].lon);
          const pos2 = latLonToVector3(ALGERIA_POINTS[j].lat, ALGERIA_POINTS[j].lon);
          
          positions.push(pos1.x, pos1.y, pos1.z);
          positions.push(pos2.x, pos2.y, pos2.z);
          
          colors.push(1, 0, 0, 0, 1, 1); // Red to Cyan gradient
        }
      }
    }
    
    return { positions: new Float32Array(positions), colors: new Float32Array(colors) };
  }, []);
  
  useFrame(({ clock }) => {
    if (particles.current) {
      particles.current.rotation.y = clock.getElapsedTime() * 0.05;
    }
    if (lines.current) {
      lines.current.rotation.y = clock.getElapsedTime() * 0.05;
    }
  });
  
  return (
    <group>
      {/* Particles (cities) */}
      <points ref={particles}>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            count={particlesData.positions.length / 3}
            array={particlesData.positions}
            itemSize={3}
          />
          <bufferAttribute
            attach="attributes-color"
            count={particlesData.colors.length / 3}
            array={particlesData.colors}
            itemSize={3}
          />
        </bufferGeometry>
        <pointsMaterial
          size={0.3}
          vertexColors
          transparent
          opacity={0.8}
          sizeAttenuation
        />
      </points>
      
      {/* Connection lines */}
      <lineSegments ref={lines}>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            count={linesData.positions.length / 3}
            array={linesData.positions}
            itemSize={3}
          />
          <bufferAttribute
            attach="attributes-color"
            count={linesData.colors.length / 3}
            array={linesData.colors}
            itemSize={3}
          />
        </bufferGeometry>
        <lineBasicMaterial
          vertexColors
          transparent
          opacity={0.4}
          linewidth={2}
        />
      </lineSegments>
      
      {/* Glowing spheres at city points */}
      {ALGERIA_POINTS.map((point, idx) => {
        const pos = latLonToVector3(point.lat, point.lon);
        return (
          <mesh key={idx} position={[pos.x, pos.y, pos.z]}>
            <sphereGeometry args={[0.1 * point.size, 16, 16]} />
            <meshBasicMaterial color="#ff0000" transparent opacity={0.8} />
          </mesh>
        );
      })}
    </group>
  );
}

// Floating particles
function FloatingParticles() {
  const particles = useRef();
  
  const particlesData = useMemo(() => {
    const count = 200;
    const positions = new Float32Array(count * 3);
    
    for (let i = 0; i < count; i++) {
      positions[i * 3] = (Math.random() - 0.5) * 20;
      positions[i * 3 + 1] = (Math.random() - 0.5) * 20;
      positions[i * 3 + 2] = (Math.random() - 0.5) * 20;
    }
    
    return positions;
  }, []);
  
  useFrame(({ clock }) => {
    if (particles.current) {
      particles.current.rotation.y = clock.getElapsedTime() * 0.02;
      particles.current.rotation.x = Math.sin(clock.getElapsedTime() * 0.1) * 0.1;
    }
  });
  
  return (
    <points ref={particles}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          count={particlesData.length / 3}
          array={particlesData}
          itemSize={3}
        />
      </bufferGeometry>
      <pointsMaterial
        size={0.05}
        color="#00ffff"
        transparent
        opacity={0.6}
        sizeAttenuation
      />
    </points>
  );
}

// Main 3D Background Component
const ThreeDBackground = () => {
  return (
    <div className="fixed inset-0 -z-10">
      <Canvas
        camera={{ position: [0, 0, 15], fov: 60 }}
        style={{ background: 'linear-gradient(180deg, #0a0a0a 0%, #1a0a0a 100%)' }}
      >
        <ambientLight intensity={0.3} />
        <pointLight position={[10, 10, 10]} intensity={0.8} color="#ff0000" />
        <pointLight position={[-10, -10, -10]} intensity={0.5} color="#00ffff" />
        
        <ParticleNetwork />
        <FloatingParticles />
      </Canvas>
      
      {/* Gradient Overlay */}
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-black/30 to-black/80 pointer-events-none" />
    </div>
  );
};

export default ThreeDBackground;
