import React, { useState, useEffect, useRef } from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceArea,
  ReferenceLine,
  CartesianGrid
} from 'recharts';
import { WaveformPoint, ApneaEvent, BradycardiaSpell } from '../types';
import {
  Play,
  Pause,
  RotateCcw,
  Radio,
  Activity,
  AlertTriangle,
  Clock,
  Eye,
  Zap
} from 'lucide-react';

interface WaveformChartProps {
  type: 'respiration' | 'heart_rate';
  data: WaveformPoint[];
  apneaEvents?: ApneaEvent[];
  bradycardiaSpells?: BradycardiaSpell[];
  title: string;
  subtitle?: string;
  unit: string;
  isDark?: boolean;
  allowPlayback?: boolean;
}

export const WaveformChart: React.FC<WaveformChartProps> = ({
  type,
  data,
  apneaEvents = [],
  bradycardiaSpells = [],
  title,
  subtitle,
  unit,
  isDark = false,
  allowPlayback = true
}) => {
  const minTime = data.length > 0 ? data[0].time_sec : 0;
  const maxTime = data.length > 0 ? data[data.length - 1].time_sec : 180;
  const totalDuration = Math.max(1, maxTime - minTime);

  // Live Playback State
  const [isLiveMode, setIsLiveMode] = useState<boolean>(false);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [playbackTime, setPlaybackTime] = useState<number>(minTime);
  const [speed, setSpeed] = useState<number>(20); // 20x default

  const playbackRef = useRef<number>(playbackTime);
  playbackRef.current = playbackTime;

  // Reset playback if data source changes
  useEffect(() => {
    setPlaybackTime(minTime);
    setIsPlaying(false);
  }, [minTime, maxTime]);

  // Playback timer interval
  useEffect(() => {
    if (!isPlaying) return;

    const intervalMs = 50; // 20 ticks per second for smooth rendering
    const timer = setInterval(() => {
      const advanceSec = (intervalMs / 1000) * speed;
      const nextTime = playbackRef.current + advanceSec;

      if (nextTime >= maxTime) {
        setPlaybackTime(maxTime);
        setIsPlaying(false);
      } else {
        setPlaybackTime(nextTime);
      }
    }, intervalMs);

    return () => clearInterval(timer);
  }, [isPlaying, speed, maxTime]);

  // Handlers
  const handleStartPlayback = () => {
    if (!isLiveMode) {
      setIsLiveMode(true);
      setPlaybackTime(minTime);
    } else if (playbackTime >= maxTime) {
      setPlaybackTime(minTime);
    }
    setIsPlaying(true);
  };

  const handlePausePlayback = () => {
    setIsPlaying(false);
  };

  const handleResetPlayback = () => {
    setIsPlaying(false);
    setPlaybackTime(minTime);
  };

  const handleExitLiveMode = () => {
    setIsPlaying(false);
    setIsLiveMode(false);
    setPlaybackTime(minTime);
  };

  const handleScrub = (newTime: number) => {
    setPlaybackTime(newTime);
  };

  // Compute active dataset based on mode
  const currentFilteredData = isLiveMode
    ? data.filter((pt) => pt.time_sec <= playbackTime)
    : data;

  // Fallback to initial point if live playback just started at minTime
  const chartData = (currentFilteredData.length > 0 ? currentFilteredData : (data.length > 0 ? [data[0]] : [])).map((pt) => ({
    time: pt.time_sec,
    value: pt.value,
  }));

  // Latest instantaneous point
  const latestPoint = currentFilteredData.length > 0
    ? currentFilteredData[currentFilteredData.length - 1]
    : (data.length > 0 ? data[0] : { time_sec: minTime, value: 0 });

  // Dynamic live event filtering
  const visibleApneaEvents = isLiveMode
    ? apneaEvents.filter((evt) => evt.start_sec <= playbackTime)
    : apneaEvents;

  const visibleBradySpells = isLiveMode
    ? bradycardiaSpells.filter((spell) => spell.start_sec <= playbackTime)
    : bradycardiaSpells;

  // Check if currently inside an active event
  const activeApneaNow = isLiveMode && apneaEvents.find(
    (e) => playbackTime >= e.start_sec && playbackTime <= e.end_sec
  );

  const activeBradyNow = isLiveMode && bradycardiaSpells.find(
    (s) => playbackTime >= s.start_sec && playbackTime <= s.end_sec
  );

  const isBradyAlarmActive = type === 'heart_rate' && latestPoint.value < 100;

  // Theme-aware chart colors
  const strokeColor = type === 'respiration'
    ? (isDark ? '#38bdf8' : '#0284c7')
    : (isDark ? '#fb7185' : '#e11d48');

  const gridColor = isDark ? '#1e293b' : '#f1f5f9';
  const axisTextColor = isDark ? '#64748b' : '#94a3b8';
  const shadedOpacity = isDark ? 0.25 : 0.15;

  const progressPercent = Math.min(100, Math.max(0, ((playbackTime - minTime) / totalDuration) * 100));

  return (
    <div className="bg-white dark:bg-slate-900 rounded-xl p-5 border border-slate-200 dark:border-slate-800 shadow-sm transition-colors duration-200 space-y-4">
      {/* Top Header & Disclaimers */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800 gap-3">
        <div>
          <div className="flex items-center gap-2">
            <span className={`w-2.5 h-2.5 rounded-full ${type === 'respiration' ? 'bg-sky-600 dark:bg-sky-400' : 'bg-rose-500 dark:bg-rose-400'}`} />
            <h4 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
              {title}
            </h4>
            {isLiveMode && (
              <span className="flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20 animate-pulse">
                <Radio className="w-2.5 h-2.5" />
                {isPlaying ? `Replay Active (${speed}x)` : 'Replay Paused'}
              </span>
            )}
          </div>
          {subtitle && <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">{subtitle}</p>}
        </div>

        {/* PERSISTENT DISCLAIMER BADGE */}
        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-50 dark:bg-amber-950/40 border border-amber-200/80 dark:border-amber-800/60 text-[11px] text-amber-800 dark:text-amber-300 font-medium">
          <span className="w-2 h-2 rounded-full bg-amber-500 shrink-0" />
          <span>
            <strong>SIMULATED REPLAY</strong> — Historical PICSDB Recording, Not Live Sensor Data
          </span>
        </div>
      </div>

      {/* LIVE CONTROLS BAR (For Waveform Monitored Patients) */}
      {allowPlayback && (
        <div className="bg-slate-50 dark:bg-slate-950/70 p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-3">
          <div className="flex flex-wrap items-center gap-2">
            {!isPlaying ? (
              <button
                onClick={handleStartPlayback}
                className="px-3.5 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold flex items-center gap-1.5 shadow-sm transition cursor-pointer"
              >
                <Play className="w-3.5 h-3.5 fill-current" />
                {isLiveMode && playbackTime < maxTime ? 'Resume Playback' : '▶ Start Live Playback'}
              </button>
            ) : (
              <button
                onClick={handlePausePlayback}
                className="px-3.5 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-700 text-white text-xs font-semibold flex items-center gap-1.5 shadow-sm transition cursor-pointer"
              >
                <Pause className="w-3.5 h-3.5 fill-current" />
                ⏸ Pause
              </button>
            )}

            {isLiveMode && (
              <>
                <button
                  onClick={handleResetPlayback}
                  className="px-2.5 py-1.5 rounded-lg bg-slate-200 dark:bg-slate-800 hover:bg-slate-300 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 text-xs font-semibold flex items-center gap-1 transition cursor-pointer"
                  title="Reset to start of window"
                >
                  <RotateCcw className="w-3 h-3" />
                  Reset
                </button>

                <button
                  onClick={handleExitLiveMode}
                  className="px-2.5 py-1.5 rounded-lg bg-slate-200/70 dark:bg-slate-800/70 hover:bg-slate-300 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-400 text-xs font-medium flex items-center gap-1 transition cursor-pointer"
                >
                  <Eye className="w-3 h-3" />
                  Static View
                </button>
              </>
            )}

            {/* Speed Selector */}
            <div className="flex items-center gap-1 bg-white dark:bg-slate-900 px-2 py-1 rounded-lg border border-slate-200 dark:border-slate-800 text-xs">
              <Zap className="w-3 h-3 text-amber-500" />
              <span className="text-[11px] text-slate-500 dark:text-slate-400 mr-1">Speed:</span>
              {[10, 20, 50].map((s) => (
                <button
                  key={s}
                  onClick={() => setSpeed(s)}
                  className={`px-1.5 py-0.5 rounded text-[10px] font-bold transition cursor-pointer ${
                    speed === s
                      ? 'bg-blue-600 text-white'
                      : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
                  }`}
                >
                  {s}x
                </button>
              ))}
            </div>
          </div>

          {/* Instantaneous Playhead Telemetry & Alerts */}
          <div className="flex items-center gap-3 text-xs">
            {isLiveMode ? (
              <div className="flex items-center gap-2">
                <div className="flex items-center gap-1.5 text-slate-600 dark:text-slate-300 font-mono text-[11px] bg-white dark:bg-slate-900 px-2.5 py-1 rounded-md border border-slate-200 dark:border-slate-800">
                  <Clock className="w-3 h-3 text-slate-400" />
                  <span>
                    {(playbackTime - minTime).toFixed(1)}s / {totalDuration.toFixed(0)}s
                  </span>
                  <span className="text-slate-400">({(playbackTime / 60).toFixed(1)}m)</span>
                </div>

                <div className={`flex items-center gap-1.5 font-mono font-bold text-xs px-2.5 py-1 rounded-md border ${
                  isBradyAlarmActive
                    ? 'bg-rose-50 dark:bg-rose-950/60 text-rose-700 dark:text-rose-300 border-rose-300 dark:border-rose-800 animate-pulse'
                    : activeApneaNow
                    ? 'bg-amber-50 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300 border-amber-300 dark:border-amber-800'
                    : 'bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 border-slate-200 dark:border-slate-800'
                }`}>
                  <Activity className="w-3 h-3 text-blue-500" />
                  <span>
                    {latestPoint.value.toFixed(1)}{unit}
                  </span>
                </div>

                {activeApneaNow && (
                  <span className="flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500 text-white animate-pulse">
                    <AlertTriangle className="w-2.5 h-2.5" />
                    APNEA EVENT #{activeApneaNow.id}
                  </span>
                )}

                {isBradyAlarmActive && (
                  <span className="flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-rose-600 text-white animate-pulse">
                    <AlertTriangle className="w-2.5 h-2.5" />
                    BRADYCARDIA &lt;100 BPM
                  </span>
                )}
              </div>
            ) : (
              <span className="text-[11px] text-slate-500 dark:text-slate-400">
                Playing at <strong>{speed}x recorded speed</strong> when active.
              </span>
            )}
          </div>
        </div>
      )}

      {/* Playback Scrubber / Timeline bar when in live mode */}
      {isLiveMode && (
        <div className="space-y-1">
          <div className="flex items-center justify-between text-[10px] text-slate-400 font-mono">
            <span>{minTime.toFixed(0)}s</span>
            <span>
              Playhead: {playbackTime.toFixed(1)}s ({progressPercent.toFixed(0)}%)
            </span>
            <span>{maxTime.toFixed(0)}s</span>
          </div>
          <input
            type="range"
            min={minTime}
            max={maxTime}
            step={0.5}
            value={playbackTime}
            onChange={(e) => handleScrub(parseFloat(e.target.value))}
            className="w-full h-1.5 bg-slate-200 dark:bg-slate-700 rounded-lg appearance-none cursor-pointer accent-blue-600"
          />
        </div>
      )}

      {/* Main Waveform Chart */}
      <div className="h-64 w-full pt-1">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 10, right: 15, left: -10, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={gridColor} vertical={false} />
            <XAxis
              dataKey="time"
              type="number"
              domain={[minTime, maxTime]}
              tickFormatter={(t) => `${t.toFixed(0)}s`}
              stroke={axisTextColor}
              fontSize={11}
              tickLine={false}
            />
            <YAxis
              stroke={axisTextColor}
              fontSize={11}
              domain={type === 'heart_rate' ? [50, 190] : ['auto', 'auto']}
              tickFormatter={(v) => `${v}${unit}`}
              tickLine={false}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: isDark ? '#0f172a' : '#ffffff',
                borderColor: isDark ? '#334155' : '#e2e8f0',
                borderRadius: '8px',
                boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
                fontSize: '12px',
                color: isDark ? '#f8fafc' : '#0f172a'
              }}
              labelFormatter={(t) => `Time: ${Number(t).toFixed(1)}s`}
              formatter={(value: any) => [`${value} ${unit}`, title]}
            />

            {/* Shaded Apnea Event Zones (Revealed dynamically in Live Mode) */}
            {type === 'respiration' &&
              visibleApneaEvents.map((evt) => {
                const start = Math.max(minTime, evt.start_sec);
                const end = isLiveMode
                  ? Math.min(playbackTime, Math.min(maxTime, evt.end_sec))
                  : Math.min(maxTime, evt.end_sec);
                if (start >= end && isLiveMode) return null;

                return (
                  <ReferenceArea
                    key={evt.id}
                    x1={start}
                    x2={end}
                    fill="#f59e0b"
                    fillOpacity={shadedOpacity}
                    stroke="#d97706"
                    strokeOpacity={0.6}
                    strokeDasharray="3 3"
                  />
                );
              })}

            {/* Bradycardia 100 BPM Reference Line & Spell Zones */}
            {type === 'heart_rate' && (
              <>
                <ReferenceLine
                  y={100}
                  stroke="#f43f5e"
                  strokeDasharray="4 4"
                  strokeWidth={1.5}
                  label={{ value: '100 BPM Limit', fill: '#fb7185', fontSize: 10, position: 'insideTopRight' }}
                />
                {visibleBradySpells.map((spell) => {
                  const start = Math.max(minTime, spell.start_sec);
                  const end = isLiveMode
                    ? Math.min(playbackTime, Math.min(maxTime, spell.end_sec))
                    : Math.min(maxTime, spell.end_sec);
                  if (start >= end && isLiveMode) return null;

                  return (
                    <ReferenceArea
                      key={spell.id}
                      x1={start}
                      x2={end}
                      fill="#f43f5e"
                      fillOpacity={shadedOpacity}
                      stroke="#e11d48"
                      strokeOpacity={0.6}
                    />
                  );
                })}
              </>
            )}

            <Line
              type="monotone"
              dataKey="value"
              stroke={strokeColor}
              strokeWidth={1.8}
              dot={false}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Chart Legend & Event Status Bar */}
      <div className="flex flex-wrap items-center justify-between text-xs text-slate-500 dark:text-slate-400 pt-1 border-t border-slate-100 dark:border-slate-800 gap-2">
        <div className="flex items-center gap-3">
          {type === 'respiration' && (
            <span className="flex items-center gap-1.5 bg-amber-50 dark:bg-amber-950/40 px-2 py-0.5 rounded text-amber-800 dark:text-amber-300 border border-amber-200 dark:border-amber-800/60">
              <span className="w-2.5 h-2.5 rounded-xs bg-amber-500/40 border border-amber-600 inline-block" />
              Apnea Pause Region ({visibleApneaEvents.length} detected)
            </span>
          )}
          {type === 'heart_rate' && (
            <>
              <span className="flex items-center gap-1.5 text-rose-700 dark:text-rose-300 bg-rose-50 dark:bg-rose-950/40 px-2 py-0.5 rounded border border-rose-200 dark:border-rose-800/60">
                <span className="w-3 h-0.5 border-t-2 border-dashed border-rose-500 inline-block" />
                100 BPM Alarm Limit
              </span>
              <span className="flex items-center gap-1.5 text-rose-700 dark:text-rose-300 bg-rose-50 dark:bg-rose-950/40 px-2 py-0.5 rounded border border-rose-200 dark:border-rose-800/60">
                <span className="w-2.5 h-2.5 rounded-xs bg-rose-500/30 border border-rose-600 inline-block" />
                Deceleration Spell ({visibleBradySpells.length} detected)
              </span>
            </>
          )}
        </div>

        {isLiveMode && (
          <span className="text-[11px] font-medium text-blue-600 dark:text-blue-400">
            Playback Status: {isPlaying ? `Streaming at ${speed}x` : 'Paused'}
          </span>
        )}
      </div>
    </div>
  );
};
