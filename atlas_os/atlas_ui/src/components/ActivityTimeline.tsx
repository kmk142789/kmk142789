import React from 'react';

type TimelineEntry = { ts: number; message: string };

type ActivityTimelineProps = {
  entries: TimelineEntry[];
};

const formatTimestamp = (ts: number): string => new Date(ts).toLocaleTimeString();

export const ActivityTimeline: React.FC<ActivityTimelineProps> = ({ entries }) => {
  const grouped = entries.reduce<Record<string, TimelineEntry[]>>((acc, entry) => {
    const bucket = new Date(entry.ts).toLocaleDateString();
    if (!acc[bucket]) {
      acc[bucket] = [];
    }
    acc[bucket].push(entry);
    return acc;
  }, {});

  return (
    <div className="activity-timeline">
      {Object.entries(grouped).map(([day, dayEntries]) => (
        <section key={day}>
          <header>{day}</header>
          <ul>
            {dayEntries.map((entry) => (
              <li key={entry.ts}>
                <time>{formatTimestamp(entry.ts)}</time>
                <span>{entry.message}</span>
              </li>
            ))}
          </ul>
        </section>
      ))}
    </div>
  );
};
