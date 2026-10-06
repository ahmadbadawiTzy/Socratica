"use client";

import React, { useEffect, useRef } from "react";
import * as THREE from "three";

interface KnowledgeGraphProps {
  className?: string;
  interactive?: boolean;
}

export default function KnowledgeGraph({
  className = "",
  interactive = true,
}: KnowledgeGraphProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const isVisibleRef = useRef<boolean>(true);
  const rafIdRef = useRef<number | null>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    // Detect dark mode
    const isDark = document.documentElement.classList.contains("dark");
    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    // Dimensions
    const width = container.clientWidth || 480;
    const height = container.clientHeight || 400;

    // Scene & Camera
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(40, width / height, 0.1, 100);
    camera.position.set(0, 0.2, 5.8);

    // Renderer
    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({
        antialias: true,
        alpha: true,
        powerPreference: "low-power",
      });
    } catch {
      return;
    }

    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));
    renderer.setClearColor(0x000000, 0);

    while (container.firstChild) {
      container.removeChild(container.firstChild);
    }
    container.appendChild(renderer.domElement);

    // Root Group for slow rotation
    const rootGroup = new THREE.Group();
    scene.add(rootGroup);

    // Colors matching editorial theme
    const coreColor = isDark ? 0x222631 : 0xe6e4dd;
    const wireColor = isDark ? 0x60a5fa : 0x2563eb;
    const satelliteColor = isDark ? 0x93c5fd : 0x1d4ed8;
    const lineColor = isDark ? 0x3b4252 : 0xc7c5be;

    // Central Knowledge Polyhedron (clean faceted icosahedron)
    const coreGeo = new THREE.IcosahedronGeometry(1.15, 1);
    const coreMat = new THREE.MeshStandardMaterial({
      color: coreColor,
      roughness: 0.35,
      metalness: 0.15,
      flatShading: true,
    });
    const coreMesh = new THREE.Mesh(coreGeo, coreMat);
    rootGroup.add(coreMesh);

    // Outer subtle wireframe cage
    const wireGeo = new THREE.IcosahedronGeometry(1.17, 1);
    const wireMat = new THREE.MeshBasicMaterial({
      color: wireColor,
      wireframe: true,
      transparent: true,
      opacity: isDark ? 0.28 : 0.22,
    });
    const wireMesh = new THREE.Mesh(wireGeo, wireMat);
    rootGroup.add(wireMesh);

    // 3 Peripheral Connected Nodes representing the Socratic cycle:
    // (1) Inquired Concept, (2) Grounded Source, (3) Synthetic Resolution
    const nodePositions: [number, number, number][] = [
      [-1.9, 0.85, -0.4],
      [1.85, 0.95, 0.3],
      [0.1, -1.8, 0.2],
    ];

    nodePositions.forEach((pos) => {
      // Small satellite node
      const nodeGeo = new THREE.IcosahedronGeometry(0.18, 0);
      const nodeMat = new THREE.MeshStandardMaterial({
        color: satelliteColor,
        roughness: 0.3,
        metalness: 0.2,
        flatShading: true,
      });
      const nodeMesh = new THREE.Mesh(nodeGeo, nodeMat);
      nodeMesh.position.set(...pos);
      rootGroup.add(nodeMesh);

      // Thin connection line to core
      const linePoints = [
        new THREE.Vector3(0, 0, 0),
        new THREE.Vector3(...pos),
      ];
      const lineGeo = new THREE.BufferGeometry().setFromPoints(linePoints);
      const lineMat = new THREE.LineBasicMaterial({
        color: lineColor,
        transparent: true,
        opacity: isDark ? 0.35 : 0.45,
      });
      const line = new THREE.Line(lineGeo, lineMat);
      rootGroup.add(line);
    });

    // Subtle orbital ring
    const ringGeo = new THREE.RingGeometry(2.1, 2.115, 48);
    const ringMat = new THREE.MeshBasicMaterial({
      color: wireColor,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: isDark ? 0.12 : 0.1,
    });
    const ringMesh = new THREE.Mesh(ringGeo, ringMat);
    ringMesh.rotation.x = Math.PI / 2.3;
    ringMesh.rotation.y = Math.PI / 12;
    rootGroup.add(ringMesh);

    // Subtle Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, isDark ? 0.75 : 0.85);
    scene.add(ambientLight);

    const keyLight = new THREE.DirectionalLight(0xffffff, isDark ? 1.4 : 1.2);
    keyLight.position.set(3, 4, 3.5);
    scene.add(keyLight);

    const fillLight = new THREE.DirectionalLight(satelliteColor, isDark ? 0.6 : 0.4);
    fillLight.position.set(-3, -2, -2);
    scene.add(fillLight);

    // Interaction handlers
    let isDragging = false;
    let prevX = 0;
    let prevY = 0;
    let targetRotY = 0;
    let targetRotX = 0;

    const onPointerDown = (e: PointerEvent) => {
      isDragging = true;
      prevX = e.clientX;
      prevY = e.clientY;
      container.style.cursor = "grabbing";
    };

    const onPointerMove = (e: PointerEvent) => {
      if (isDragging) {
        const dx = e.clientX - prevX;
        const dy = e.clientY - prevY;
        rootGroup.rotation.y += dx * 0.005;
        rootGroup.rotation.x += dy * 0.005;
        prevX = e.clientX;
        prevY = e.clientY;
      } else {
        const rect = container.getBoundingClientRect();
        const nx = ((e.clientX - rect.left) / rect.width) * 2 - 1;
        const ny = -((e.clientY - rect.top) / rect.height) * 2 + 1;
        targetRotY = nx * 0.25;
        targetRotX = -ny * 0.18;
      }
    };

    const onPointerUp = () => {
      isDragging = false;
      container.style.cursor = "grab";
    };

    if (interactive) {
      container.addEventListener("pointerdown", onPointerDown);
      window.addEventListener("pointermove", onPointerMove);
      window.addEventListener("pointerup", onPointerUp);
      container.style.cursor = "grab";
    }

    // Resize handler
    const handleResize = () => {
      if (!container || !renderer) return;
      const w = container.clientWidth || 480;
      const h = container.clientHeight || 400;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };

    const resizeObserver = new ResizeObserver(handleResize);
    resizeObserver.observe(container);

    // IntersectionObserver to pause rendering when out of viewport
    const intersectionObserver = new IntersectionObserver(
      (entries) => {
        const entry = entries[0];
        isVisibleRef.current = entry.isIntersecting;
      },
      { threshold: 0.1 }
    );
    intersectionObserver.observe(container);

    // Animation Loop
    const clock = new THREE.Clock();

    const renderFrame = () => {
      if (!isVisibleRef.current || document.hidden) {
        rafIdRef.current = requestAnimationFrame(renderFrame);
        return;
      }

      const delta = clock.getDelta();

      if (!prefersReducedMotion) {
        if (!isDragging) {
          // Slow, calm continuous rotation with subtle pointer influence
          rootGroup.rotation.y += delta * 0.18 + targetRotY * 0.01;
          rootGroup.rotation.x += (targetRotX - rootGroup.rotation.x) * 0.04;
          ringMesh.rotation.z += delta * 0.05;
        }
      }

      renderer.render(scene, camera);

      if (!prefersReducedMotion) {
        rafIdRef.current = requestAnimationFrame(renderFrame);
      }
    };

    if (prefersReducedMotion) {
      renderer.render(scene, camera);
    } else {
      rafIdRef.current = requestAnimationFrame(renderFrame);
    }

    // Cleanup
    return () => {
      if (rafIdRef.current) cancelAnimationFrame(rafIdRef.current);
      if (interactive) {
        container.removeEventListener("pointerdown", onPointerDown);
        window.removeEventListener("pointermove", onPointerMove);
        window.removeEventListener("pointerup", onPointerUp);
      }
      resizeObserver.disconnect();
      intersectionObserver.disconnect();

      scene.traverse((obj) => {
        if (obj instanceof THREE.Mesh || obj instanceof THREE.Line) {
          obj.geometry?.dispose();
          if (Array.isArray(obj.material)) {
            obj.material.forEach((m) => m.dispose());
          } else {
            obj.material?.dispose();
          }
        }
      });

      renderer.dispose();
      while (container.firstChild) {
        container.removeChild(container.firstChild);
      }
    };
  }, [interactive]);

  return (
    <div
      ref={containerRef}
      className={`relative w-full h-[320px] sm:h-[380px] lg:h-[440px] select-none touch-none ${className}`}
      role="img"
      aria-label="Abstract geometric 3D visualization representing connected academic knowledge"
    />
  );
}
