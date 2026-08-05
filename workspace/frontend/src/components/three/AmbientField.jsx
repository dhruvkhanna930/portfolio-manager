/**
 * Ambient particle field for the Home hero (CLAUDE.md §15.1).
 *
 * Decorative ONLY. It encodes exactly one thing -- the sign and rough magnitude
 * of today's P/L, as a colour tint -- and even that is duplicated as a real
 * number in the KPI cards next to it. Nothing here is the sole carrier of any
 * fact, so if WebGL is unavailable the page loses nothing but the flourish.
 *
 * Deliberately not a 3D chart: §15.1 rules those out because depth and
 * perspective distort perceived value.
 */

import { Suspense, useMemo, useRef, useState } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import * as THREE from 'three'

const PARTICLE_COUNT = 1400
const FIELD_WIDTH = 26
const FIELD_DEPTH = 14

// Reading the palette from the CSS custom properties keeps this in the §8.1
// token system -- change --positive there and the hero follows.
function readToken(name, fallback) {
  if (typeof window === 'undefined') return fallback
  const value = getComputedStyle(document.documentElement).getPropertyValue(name).trim()
  return value || fallback
}

const vertexShader = /* glsl */ `
  uniform float uTime;
  uniform float uAmplitude;
  attribute float aScale;
  attribute float aOffset;
  varying float vFade;

  void main() {
    vec3 pos = position;
    // Two out-of-phase waves so the surface never looks like it's marching in
    // lockstep, which is what makes a particle field read as mechanical.
    pos.y += sin(uTime * 0.32 + pos.x * 0.22 + aOffset) * uAmplitude;
    pos.y += cos(uTime * 0.21 + pos.z * 0.31 + aOffset) * uAmplitude * 0.6;

    vec4 mvPosition = modelViewMatrix * vec4(pos, 1.0);
    gl_Position = projectionMatrix * mvPosition;
    gl_PointSize = aScale * (34.0 / -mvPosition.z);

    // Fade with distance from the centre so the field dissolves at the edges
    // instead of ending on a hard rectangle.
    float dist = length(pos.xz) / ${(FIELD_WIDTH / 2).toFixed(1)};
    vFade = smoothstep(1.0, 0.15, dist);
  }
`

const fragmentShader = /* glsl */ `
  uniform vec3 uColor;
  uniform float uOpacity;
  varying float vFade;

  void main() {
    // Round, soft-edged points -- square GL points look like dead pixels.
    float d = length(gl_PointCoord - vec2(0.5));
    if (d > 0.5) discard;
    float alpha = smoothstep(0.5, 0.0, d) * vFade * uOpacity;
    gl_FragColor = vec4(uColor, alpha);
  }
`

function Field({ color, amplitude, opacity }) {
  const materialRef = useRef()
  const pointsRef = useRef()

  const [positions, scales, offsets] = useMemo(() => {
    const pos = new Float32Array(PARTICLE_COUNT * 3)
    const scl = new Float32Array(PARTICLE_COUNT)
    const off = new Float32Array(PARTICLE_COUNT)
    for (let i = 0; i < PARTICLE_COUNT; i += 1) {
      pos[i * 3] = (Math.random() - 0.5) * FIELD_WIDTH
      pos[i * 3 + 1] = (Math.random() - 0.5) * 1.4
      pos[i * 3 + 2] = (Math.random() - 0.5) * FIELD_DEPTH
      scl[i] = 0.5 + Math.random() * 1.6
      off[i] = Math.random() * Math.PI * 2
    }
    return [pos, scl, off]
  }, [])

  const uniforms = useMemo(
    () => ({
      uTime: { value: 0 },
      uAmplitude: { value: amplitude },
      uColor: { value: new THREE.Color(color) },
      uOpacity: { value: opacity },
    }),
    // Built once; live values are pushed in useFrame below so a colour change
    // doesn't rebuild the geometry.
    [] // eslint-disable-line react-hooks/exhaustive-deps
  )

  useFrame((state, delta) => {
    const material = materialRef.current
    if (!material) return
    material.uniforms.uTime.value += delta
    material.uniforms.uAmplitude.value = amplitude
    material.uniforms.uOpacity.value = opacity
    // Ease toward the target colour so a P/L flip is a settle, not a snap.
    material.uniforms.uColor.value.lerp(new THREE.Color(color), Math.min(1, delta * 1.5))
    if (pointsRef.current) pointsRef.current.rotation.y += delta * 0.014
  })

  return (
    <points ref={pointsRef} rotation={[-0.42, 0, 0]}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} />
        <bufferAttribute attach="attributes-aScale" args={[scales, 1]} />
        <bufferAttribute attach="attributes-aOffset" args={[offsets, 1]} />
      </bufferGeometry>
      <shaderMaterial
        ref={materialRef}
        uniforms={uniforms}
        vertexShader={vertexShader}
        fragmentShader={fragmentShader}
        transparent
        depthWrite={false}
        blending={THREE.AdditiveBlending}
      />
    </points>
  )
}

/**
 * @param {number} intensity -1..1 -- today's P/L direction and strength.
 *   Only used to pick a colour between --negative and --positive.
 */
export default function AmbientField({ intensity = 0, className = '' }) {
  const [failed, setFailed] = useState(false)

  const reducedMotion =
    typeof window !== 'undefined' &&
    window.matchMedia?.('(prefers-reduced-motion: reduce)').matches

  const { color, amplitude, opacity } = useMemo(() => {
    const positive = readToken('--positive', '#16C784')
    const negative = readToken('--negative', '#F6465D')
    const accent = readToken('--accent', '#22D3A6')
    const clamped = Math.max(-1, Math.min(1, intensity))
    const magnitude = Math.abs(clamped)

    // Near-flat days stay on the brand accent rather than committing to a
    // green or red story the numbers don't support.
    const target = new THREE.Color(accent)
    if (magnitude > 0.02) {
      target.lerp(new THREE.Color(clamped > 0 ? positive : negative), Math.min(1, magnitude * 1.6))
    }
    return {
      color: `#${target.getHexString()}`,
      amplitude: reducedMotion ? 0 : 0.26 + magnitude * 0.5,
      opacity: 0.5,
    }
  }, [intensity, reducedMotion])

  if (failed) return null

  return (
    <div
      aria-hidden="true"
      className={`pointer-events-none absolute inset-0 overflow-hidden ${className}`}
      style={{
        // Dissolve into the card rather than ending at its edges.
        maskImage: 'radial-gradient(120% 100% at 70% 45%, #000 25%, transparent 78%)',
        WebkitMaskImage: 'radial-gradient(120% 100% at 70% 45%, #000 25%, transparent 78%)',
      }}
    >
      <Canvas
        dpr={[1, 1.5]}
        camera={{ position: [0, 1.6, 11], fov: 55 }}
        gl={{ antialias: false, alpha: true, powerPreference: 'low-power' }}
        frameloop={reducedMotion ? 'demand' : 'always'}
        onCreated={({ gl }) => gl.setClearColor(0x000000, 0)}
        // A missing/blocked WebGL context must degrade to "no decoration",
        // never to a broken page.
        fallback={null}
        onError={() => setFailed(true)}
      >
        <Suspense fallback={null}>
          <Field color={color} amplitude={amplitude} opacity={opacity} />
        </Suspense>
      </Canvas>
    </div>
  )
}
