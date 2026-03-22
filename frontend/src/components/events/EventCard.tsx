'use client';

import Image from 'next/image';
import { motion } from 'framer-motion';
import { CalendarDays, MapPin } from 'lucide-react';
import { formatEventDateLabel } from '@/data/mockEvents';
import type { EventRecord } from '@/types/eventDiscovery';

interface EventCardProps {
  event: EventRecord;
  index: number;
}

const badgeMotion = {
  rest: { scale: 1, y: 0 },
  hover: { scale: 1.03, y: -1 },
};

export function EventCard({ event, index }: EventCardProps) {
  return (
    <motion.article
      initial={{ opacity: 0, y: 26 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, delay: index * 0.05, ease: 'easeOut' }}
      whileHover={{ y: -8 }}
      className="group relative overflow-hidden rounded-[24px] border border-[#EAEAEA] bg-white shadow-[0_24px_70px_-34px_rgba(13,71,161,0.2)]"
    >
      <div className="absolute inset-x-5 top-0 h-[2px] bg-[linear-gradient(90deg,#0D47A1,#4285F4,#34A853)]" />
      <div className="relative overflow-hidden">
        <div className="absolute inset-0 z-10 bg-gradient-to-t from-[#0D47A1]/70 via-[#0D47A1]/10 to-transparent" />
        <motion.div
          whileHover={{ scale: 1.06 }}
          transition={{ duration: 0.7, ease: 'easeOut' }}
          className="relative h-52 overflow-hidden sm:h-56 lg:h-60"
        >
          <Image
            src={event.image.src}
            alt={event.image.alt}
            fill
            sizes="(min-width: 1280px) 30vw, (min-width: 768px) 45vw, 100vw"
            className="object-cover"
          />
        </motion.div>

        <div className="absolute left-4 top-4 z-20 flex max-w-[calc(100%-2rem)] flex-wrap items-center gap-2">
          <motion.span
            variants={badgeMotion}
            initial="rest"
            whileHover="hover"
            className="rounded-full border border-[#4285F4]/30 bg-[#0D47A1]/88 px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.22em] text-white sm:text-[11px]"
          >
            {event.category}
          </motion.span>
          <motion.span
            variants={badgeMotion}
            initial="rest"
            whileHover="hover"
            className={`rounded-full px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.22em] sm:text-[11px] ${
              event.priceType === 'Free'
                ? 'border border-[#34A853]/30 bg-[#34A853]/90 text-white'
                : 'border border-[#FBBC05]/35 bg-[#FBBC05]/92 text-[#0D47A1]'
            }`}
          >
            {event.priceLabel}
          </motion.span>
        </div>
      </div>

      <div className="relative space-y-4 p-5 sm:space-y-5 sm:p-6">
        <div className="space-y-3">
          <h3 className="text-xl font-semibold tracking-[-0.03em] text-[#0D47A1] sm:text-2xl">
            {event.title}
          </h3>
          <p className="line-clamp-3 text-sm leading-6 text-[#666666]">
            {event.description}
          </p>
        </div>

        <div className="space-y-3 text-sm text-[#666666]">
          <div className="flex items-start gap-3">
            <div className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[#4285F4] text-white shadow-[0_10px_24px_-12px_rgba(66,133,244,0.75)]">
              <CalendarDays className="h-4 w-4" />
            </div>
            <span className="leading-6">{formatEventDateLabel(event.startsAt)}</span>
          </div>
          <div className="flex items-start gap-3">
            <div className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[#F4F8FA] text-[#34A853] ring-1 ring-[#EAEAEA]">
              <MapPin className="h-4 w-4" />
            </div>
            <span className="leading-6">
              {event.location}, {event.city}
            </span>
          </div>
        </div>

        <motion.button
          type="button"
          whileHover={{ scale: 1.01 }}
          whileTap={{ scale: 0.99 }}
          className="inline-flex w-full items-center justify-center rounded-full bg-[#0D47A1] px-5 py-3 text-sm font-medium text-white transition-colors duration-300 hover:bg-[#4285F4]"
        >
          View Details
        </motion.button>
      </div>
    </motion.article>
  );
}
