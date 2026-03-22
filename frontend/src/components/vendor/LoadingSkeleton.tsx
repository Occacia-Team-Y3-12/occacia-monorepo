'use client';

export function LoadingSkeleton() {
  return (
    <div className="space-y-4 py-8">
      {[...Array(3)].map((_, i) => (
        <div key={i} className="animate-pulse">
          <div className="bg-gray-200 rounded-lg h-40 flex flex-col gap-4 p-6">
            <div className="h-4 bg-gray-300 rounded w-1/2"></div>
            <div className="h-4 bg-gray-300 rounded w-3/4"></div>
            <div className="flex gap-4">
              <div className="h-6 bg-gray-300 rounded w-20"></div>
              <div className="h-6 bg-gray-300 rounded w-20"></div>
              <div className="h-6 bg-gray-300 rounded w-24"></div>
            </div>
            <div className="h-4 bg-gray-300 rounded w-1/3 mt-2"></div>
          </div>
        </div>
      ))}
    </div>
  );
}
