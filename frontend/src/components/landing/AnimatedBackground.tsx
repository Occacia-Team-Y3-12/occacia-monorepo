'use client';

import { useEffect, useRef } from 'react';

type Bubble = {
  x: number;
  y: number;
  r: number;
  speed: number;
  color: string;
  drift: number;
};

type Dot = {
  x: number;
  y: number;
  vx: number;
  vy: number;
};

const COLORS = ['#0D47A1', '#4285F4', '#9BB9E8', '#C9C9C9', '#CCCCCC'];

const random = (min: number, max: number) => Math.random() * (max - min) + min;

export default function AnimatedBackground() {
  const orbsRef = useRef<HTMLCanvasElement | null>(null);
  const networkRef = useRef<HTMLCanvasElement | null>(null);
  const bubblesRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const orbsCanvas = orbsRef.current;
    const networkCanvas = networkRef.current;
    const bubblesCanvas = bubblesRef.current;

    if (!orbsCanvas || !networkCanvas || !bubblesCanvas) return;

    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const orbCtx = orbsCanvas.getContext('2d');
    const networkCtx = networkCanvas.getContext('2d');
    const bubbleCtx = bubblesCanvas.getContext('2d');
    if (!orbCtx || !networkCtx || !bubbleCtx) return;

    const dots: Dot[] = Array.from({ length: 40 }, () => ({
      x: random(0, window.innerWidth),
      y: random(0, window.innerHeight),
      vx: random(-0.25, 0.25),
      vy: random(-0.25, 0.25),
    }));

    const bubbles: Bubble[] = Array.from({ length: 28 }, () => ({
      x: random(0, window.innerWidth),
      y: random(0, window.innerHeight),
      r: random(6, 28),
      speed: random(0.2, 0.7),
      color: COLORS[Math.floor(random(0, COLORS.length))],
      drift: random(-0.2, 0.2),
    }));

    let rafId = 0;
    let width = 0;
    let height = 0;

    const setSize = () => {
      width = window.innerWidth;
      height = window.innerHeight;

      [orbsCanvas, networkCanvas, bubblesCanvas].forEach((canvas) => {
        canvas.width = width * dpr;
        canvas.height = height * dpr;
        canvas.style.width = `${width}px`;
        canvas.style.height = `${height}px`;
      });

      orbCtx.setTransform(dpr, 0, 0, dpr, 0, 0);
      networkCtx.setTransform(dpr, 0, 0, dpr, 0, 0);
      bubbleCtx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };

    const draw = (time: number) => {
      orbCtx.clearRect(0, 0, width, height);
      networkCtx.clearRect(0, 0, width, height);
      bubbleCtx.clearRect(0, 0, width, height);

      const t = time * 0.0002;

      const gradients = [
        { x: width * 0.18 + Math.sin(t) * 28, y: height * 0.25, r: 220, color: '#4285F4' },
        { x: width * 0.5 + Math.cos(t * 1.4) * 26, y: height * 0.16, r: 200, color: '#0D47A1' },
        { x: width * 0.82 + Math.sin(t * 1.2) * 20, y: height * 0.32, r: 200, color: '#9BB9E8' },
        { x: width * 0.72, y: height * 0.78 + Math.cos(t * 0.8) * 20, r: 180, color: '#C9C9C9' },
      ];

      gradients.forEach((g) => {
        const grad = orbCtx.createRadialGradient(g.x, g.y, 0, g.x, g.y, g.r);
        grad.addColorStop(0, `${g.color}22`);
        grad.addColorStop(1, `${g.color}00`);
        orbCtx.fillStyle = grad;
        orbCtx.beginPath();
        orbCtx.arc(g.x, g.y, g.r, 0, Math.PI * 2);
        orbCtx.fill();
      });

      dots.forEach((dot) => {
        dot.x += dot.vx;
        dot.y += dot.vy;

        if (dot.x < -10 || dot.x > width + 10) dot.vx *= -1;
        if (dot.y < -10 || dot.y > height + 10) dot.vy *= -1;
      });

      for (let i = 0; i < dots.length; i += 1) {
        for (let j = i + 1; j < dots.length; j += 1) {
          const dx = dots[i].x - dots[j].x;
          const dy = dots[i].y - dots[j].y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist > 130) continue;

          networkCtx.strokeStyle = `rgba(66,133,244,${(1 - dist / 130) * 0.25})`;
          networkCtx.lineWidth = 1;
          networkCtx.beginPath();
          networkCtx.moveTo(dots[i].x, dots[i].y);
          networkCtx.lineTo(dots[j].x, dots[j].y);
          networkCtx.stroke();
        }
      }

      dots.forEach((dot) => {
        networkCtx.fillStyle = 'rgba(13,71,161,0.45)';
        networkCtx.beginPath();
        networkCtx.arc(dot.x, dot.y, 1.6, 0, Math.PI * 2);
        networkCtx.fill();
      });

      bubbles.forEach((bubble) => {
        bubble.y -= bubble.speed;
        bubble.x += bubble.drift;

        if (bubble.y + bubble.r < 0) {
          bubble.y = height + bubble.r + random(0, 120);
          bubble.x = random(0, width);
          bubble.r = random(6, 28);
          bubble.speed = random(0.2, 0.7);
          bubble.color = COLORS[Math.floor(random(0, COLORS.length))];
          bubble.drift = random(-0.2, 0.2);
        }

        bubbleCtx.fillStyle = `${bubble.color}22`;
        bubbleCtx.strokeStyle = `${bubble.color}66`;
        bubbleCtx.lineWidth = 1.4;
        bubbleCtx.beginPath();
        bubbleCtx.arc(bubble.x, bubble.y, bubble.r, 0, Math.PI * 2);
        bubbleCtx.fill();
        bubbleCtx.stroke();

        bubbleCtx.fillStyle = '#FFFFFFAA';
        bubbleCtx.beginPath();
        bubbleCtx.arc(bubble.x - bubble.r * 0.34, bubble.y - bubble.r * 0.36, Math.max(1.8, bubble.r * 0.13), 0, Math.PI * 2);
        bubbleCtx.fill();
      });

      rafId = window.requestAnimationFrame(draw);
    };

    setSize();
    rafId = window.requestAnimationFrame(draw);
    window.addEventListener('resize', setSize);

    return () => {
      window.cancelAnimationFrame(rafId);
      window.removeEventListener('resize', setSize);
    };
  }, []);

  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden">
      <canvas ref={orbsRef} className="absolute inset-0" />
      <canvas ref={networkRef} className="absolute inset-0 opacity-80" />
      <canvas ref={bubblesRef} className="absolute inset-0 opacity-90" />
    </div>
  );
}
