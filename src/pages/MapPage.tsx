import { useEffect, useMemo, useRef, useState } from "react";
import { GeoJSON, MapContainer, TileLayer, useMap } from "react-leaflet";
import { useSearchParams } from "react-router-dom";
import type { Feature, FeatureCollection, GeoJsonObject } from "geojson";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import LevelPill from "../components/LevelPill";
import { API_ORIGIN, api, type MapSpot } from "../lib/load";
import { usePrefs } from "../lib/prefs";
import { LEVELS } from "../lib/vitality";
import type { VitalityLevel } from "../types";

type Nation = {
  id: string;
  sido: string;
  name: string;
  lat: number;
  lng: number;
  gwh: number;
  rankLevel: VitalityLevel;
  score: number;
  level: VitalityLevel;
  vitalRank: VitalityLevel;
  salesKind: "실측" | "추론";
  flpopKind: "실측" | "추론";
  netKind: "실측" | "추론";
};

function asNation(props: GeoJsonObject | Feature["properties"]): Nation {
  const row = props as Nation;
  return row;
}

type Shops = { lats: Float32Array; lngs: Float32Array; buckets: Map<number, number[]> };

const STREET = ["#2f9e5f", "#7cbc3d", "#e3c34a", "#e07b2e", "#d63a2f"];

function bucketKey(lat: number, lng: number) {
  return Math.floor(lat * 20) * 10000 + Math.floor(lng * 20);
}

function StreetHeat() {
  const map = useMap();
  const shops = useRef<Shops | null>(null);

  useEffect(() => {
    let cancel = false;
    fetch(`${API_ORIGIN}/data/processed/national_stores.bin`)
      .then((res) => res.arrayBuffer())
      .then((buf) => {
        if (cancel) return;
        const view = new DataView(buf);
        const count = view.getUint32(4, true);
        const lats = new Float32Array(count);
        const lngs = new Float32Array(count);
        const buckets = new Map<number, number[]>();
        let offset = 8;
        for (let i = 0; i < count; i++) {
          const lat = view.getInt32(offset + 1, true) / 1e6;
          const lng = view.getInt32(offset + 5, true) / 1e6;
          lats[i] = lat;
          lngs[i] = lng;
          const key = bucketKey(lat, lng);
          const list = buckets.get(key);
          if (list) list.push(i);
          else buckets.set(key, [i]);
          offset += 9;
        }
        shops.current = { lats, lngs, buckets };
        map.fire("moveend");
      })
      .catch(() => undefined);
    return () => {
      cancel = true;
    };
  }, [map]);

  useEffect(() => {
    const pane = map.getPane("street") ?? map.createPane("street");
    pane.style.zIndex = "450";
    pane.style.pointerEvents = "none";
    const canvas = document.createElement("canvas");
    pane.appendChild(canvas);
    const fade = () => {
      const shown = Math.min(1, Math.max(0, (map.getZoom() - 11) / 1.6));
      pane.style.opacity = String(shown);
    };
    let zooming = false;
    let wait = 0;
    let frame = 0;
    const draw = () => {
      fade();
      const ctx = canvas.getContext("2d");
      if (!ctx) return;
      if (map.getZoom() < 10.6) {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        return;
      }
      const size = map.getSize();
      const ratio = window.devicePixelRatio || 1;
      const nextW = Math.round(size.x * ratio);
      const nextH = Math.round(size.y * ratio);
      if (canvas.width !== nextW || canvas.height !== nextH) {
        canvas.width = nextW;
        canvas.height = nextH;
        canvas.style.width = `${size.x}px`;
        canvas.style.height = `${size.y}px`;
      }
      const origin = map.containerPointToLayerPoint([0, 0]);
      L.DomUtil.setPosition(canvas, origin);
      const data = shops.current;
      ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
      ctx.clearRect(0, 0, size.x, size.y);
      if (!data) return;
      const bounds = map.getBounds();
      const south = bounds.getSouth();
      const north = bounds.getNorth();
      const west = bounds.getWest();
      const east = bounds.getEast();
      const zoom = map.getZoom();
      const cell = zoom >= 15 ? 0.0018 : zoom >= 13 ? 0.0032 : 0.0055;
      const hits: number[] = [];
      for (let i = Math.floor(south * 20); i <= Math.floor(north * 20); i++) {
        for (let j = Math.floor(west * 20); j <= Math.floor(east * 20); j++) {
          const list = data.buckets.get(i * 10000 + j);
          if (!list) continue;
          for (const index of list) {
            const lat = data.lats[index];
            const lng = data.lngs[index];
            if (lat >= south && lat <= north && lng >= west && lng <= east) hits.push(index);
          }
        }
      }
      const stride = hits.length > 20000 ? Math.ceil(hits.length / 20000) : 1;
      const counts = new Map<number, number>();
      for (let n = 0; n < hits.length; n += stride) {
        const lat = data.lats[hits[n]];
        const lng = data.lngs[hits[n]];
        const key = Math.floor(lat / cell) * 100000 + Math.floor(lng / cell);
        counts.set(key, (counts.get(key) ?? 0) + 1);
      }
      const ordered = [...counts.values()].sort((a, b) => a - b);
      const denom = Math.max(ordered.length, 1);
      const colorOf = new Map<number, number>();
      for (const [key, count] of counts) {
        let lo = 0;
        let hi = ordered.length;
        while (lo < hi) {
          const mid = (lo + hi) >> 1;
          if (ordered[mid] < count) lo = mid + 1;
          else hi = mid;
        }
        colorOf.set(key, Math.min(4, Math.floor((lo * 5) / denom)));
      }
      const radius = 1.5 + Math.min(2, Math.max(0, zoom - 12) * 0.45);
      const groups: number[][] = [[], [], [], [], []];
      for (let n = 0; n < hits.length; n += stride) {
        const lat = data.lats[hits[n]];
        const lng = data.lngs[hits[n]];
        const key = Math.floor(lat / cell) * 100000 + Math.floor(lng / cell);
        groups[colorOf.get(key) ?? 0].push(hits[n]);
      }
      ctx.globalAlpha = 0.45;
      for (let color = 0; color < groups.length; color++) {
        const group = groups[color];
        if (!group.length) continue;
        ctx.beginPath();
        ctx.fillStyle = STREET[color];
        for (const index of group) {
          const point = map.latLngToLayerPoint([data.lats[index], data.lngs[index]]);
          ctx.moveTo(point.x - origin.x + radius, point.y - origin.y);
          ctx.arc(point.x - origin.x, point.y - origin.y, radius, 0, Math.PI * 2);
        }
        ctx.fill();
      }
    };
    const schedule = () => {
      if (zooming) return;
      window.clearTimeout(wait);
      window.cancelAnimationFrame(frame);
      wait = window.setTimeout(() => {
        frame = window.requestAnimationFrame(draw);
      }, 80);
    };
    const onZoomStart = () => {
      zooming = true;
      window.clearTimeout(wait);
      fade();
    };
    const onZoomEnd = () => {
      zooming = false;
      schedule();
    };
    map.on("zoomstart", onZoomStart);
    map.on("zoom", fade);
    map.on("zoomend", onZoomEnd);
    map.on("moveend resize", schedule);
    draw();
    return () => {
      window.clearTimeout(wait);
      window.cancelAnimationFrame(frame);
      map.off("zoomstart", onZoomStart);
      map.off("zoom", fade);
      map.off("zoomend", onZoomEnd);
      map.off("moveend resize", schedule);
      canvas.remove();
    };
  }, [map]);

  return null;
}

function FlyTo({ lat, lng }: { lat: number; lng: number }) {
  const map = useMap();
  useEffect(() => {
    map.flyTo([lat, lng], 12.5, { duration: 1.15 });
  }, [lat, lng, map]);
  return null;
}

function MarkTarget({ sido, name, color }: { sido: string; name: string; color: string }) {
  const map = useMap();
  useEffect(() => {
    if (!sido || !name) return;
    let opened = false;
    const mark = (open: boolean) => {
      map.eachLayer((layer) => {
        const feature = (layer as L.Layer & { feature?: Feature }).feature;
        if (!feature?.properties) return;
        const row = asNation(feature.properties);
        if (row.sido !== sido || row.name !== name) return;
        const path = layer as L.Path;
        path.setStyle({ weight: 3.2, color });
        path.bringToFront();
        if (open && !opened) {
          path.openPopup();
          opened = true;
        }
      });
    };
    mark(map.getZoom() >= 11);
    const afterMove = () => mark(true);
    const restyle = () => mark(false);
    map.on("moveend", afterMove);
    map.on("zoomend", restyle);
    return () => {
      map.off("moveend", afterMove);
      map.off("zoomend", restyle);
    };
  }, [map, sido, name, color]);
  return null;
}

function ZoomPaint({
  colorMode,
  sidoRank,
  sidoPower,
  stroke,
}: {
  colorMode: "활력" | "전력";
  sidoRank: Map<string, VitalityLevel>;
  sidoPower: Map<string, VitalityLevel>;
  stroke: string;
}) {
  const map = useMap();
  useEffect(() => {
    const pane = map.getPane("overlayPane");
    let band = map.getZoom() < 8 ? 0 : 1;
    let shown = 0.18;
    const paint = () => {
      const zoom = map.getZoom();
      const alley = Math.min(1, Math.max(0, (zoom - 11) / 1.6));
      const fillOpacity = 0.18 - 0.13 * alley;
      if (pane) pane.style.setProperty("--area-fill", fillOpacity.toFixed(3));
      const next = zoom < 8 ? 0 : 1;
      if (next === band && Math.abs(fillOpacity - shown) < 0.01) return;
      band = next;
      shown = fillOpacity;
      map.eachLayer((layer) => {
        const feature = (layer as L.Layer & { feature?: Feature }).feature;
        if (!feature?.properties) return;
        const row = asNation(feature.properties);
        const level =
          next === 0
            ? ((colorMode === "전력" ? sidoPower : sidoRank).get(row.sido) ?? 3)
            : colorMode === "전력"
              ? row.rankLevel
              : row.vitalRank;
        (layer as L.Path).setStyle({
          color: stroke,
          weight: 1.15,
          opacity: 0.45,
          fillColor: LEVELS[level].color,
          fillOpacity,
        });
      });
    };
    map.on("zoomend", paint);
    return () => {
      map.off("zoomend", paint);
    };
  }, [map, colorMode, sidoRank, sidoPower, stroke]);
  return null;
}

function RememberZoom({ zoomRef }: { zoomRef: { current: number } }) {
  const map = useMap();
  useEffect(() => {
    const send = () => {
      zoomRef.current = map.getZoom();
    };
    send();
    map.on("zoomend", send);
    return () => {
      map.off("zoomend", send);
    };
  }, [map, zoomRef]);
  return null;
}

export default function MapPage() {
  const { t, theme, lang, level } = usePrefs();
  const [params] = useSearchParams();
  const targetSido = params.get("sido") ?? "";
  const targetName = params.get("name") ?? "";
  const stroke = theme === "dark" ? "#d5e4f2" : "#1c2b3a";
  const markColor = theme === "dark" ? "#3ec6ef" : "#003068";
  const [spots, setSpots] = useState<MapSpot[]>([]);
  const [geo, setGeo] = useState<FeatureCollection | null>(null);
  const [q, setQ] = useState("");
  const zoomRef = useRef(7);
  const [colorMode, setColorMode] = useState<"활력" | "전력">(params.get("color") === "전력" ? "전력" : "활력");
  const [focus, setFocus] = useState<{ lat: number; lng: number } | null>(null);
  const [picked, setPicked] = useState<Nation | MapSpot | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!geo || !targetSido || !targetName) return;
    const feat = geo.features.find((item) => {
      const row = asNation(item.properties);
      return row.sido === targetSido && row.name === targetName;
    });
    if (!feat) return;
    const row = asNation(feat.properties);
    setPicked(row);
    setFocus({ lat: row.lat, lng: row.lng });
  }, [geo, targetSido, targetName]);

  useEffect(() => {
    api.map().then((d) => setSpots(d.spots)).catch(() => setSpots([]));
    fetch(`${API_ORIGIN}/data/processed/national_map.geojson?v=vital`)
      .then((res) => {
        if (!res.ok) throw new Error(String(res.status));
        return res.json() as Promise<FeatureCollection>;
      })
      .then(setGeo)
      .catch(() => setError(t("mapMiss")));
  }, []);

  const areas = useMemo(
    () => (geo ? geo.features.map((feat) => asNation(feat.properties)) : []),
    [geo],
  );
  const sidoRank = useMemo(() => {
    const bucket = new Map<string, { sum: number; n: number }>();
    for (const area of areas) {
      const row = bucket.get(area.sido) ?? { sum: 0, n: 0 };
      row.sum += area.score;
      row.n += 1;
      bucket.set(area.sido, row);
    }
    const means = [...bucket.entries()].map(([sido, row]) => ({ sido, mean: row.sum / row.n }));
    means.sort((a, b) => a.mean - b.mean);
    const rank = new Map<string, VitalityLevel>();
    means.forEach((row, index) => {
      rank.set(row.sido, Math.min(5, Math.floor((index * 5) / means.length) + 1) as VitalityLevel);
    });
    return rank;
  }, [areas]);
  const sidoPower = useMemo(() => {
    const bucket = new Map<string, number>();
    for (const area of areas) bucket.set(area.sido, (bucket.get(area.sido) ?? 0) + area.gwh);
    const means = [...bucket.entries()].sort((a, b) => a[1] - b[1]);
    const rank = new Map<string, VitalityLevel>();
    means.forEach(([sido], index) => {
      rank.set(sido, Math.min(5, Math.floor((index * 5) / means.length) + 1) as VitalityLevel);
    });
    return rank;
  }, [areas]);
  const hits = useMemo(() => {
    const needle = q.trim();
    if (!needle) return [];
    return [
      ...areas.filter((area) => area.name.includes(needle) || area.sido.includes(needle)),
      ...spots.filter((spot) => spot.name.includes(needle) || spot.district.includes(needle)),
    ].slice(0, 8);
  }, [q, areas, spots]);

  function isSpot(row: Nation | MapSpot): row is MapSpot {
    return "district" in row && "industryBias" in row;
  }

  if (error) return <p>{error}</p>;

  return (
    <div className="map-page">
      <div className="page-head">
        <h1 className="map-title">{t("mapTitle")}</h1>
      </div>
      <div className="map-wrap">
        <div className="map-panel">
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder={t("mapPh")} />
          {hits.length > 0 && (
            <ul className="search-hits">
              {hits.map((hit) => (
                <li key={isSpot(hit) ? hit.id : hit.id}>
                  <button
                    onClick={() => {
                      setFocus({ lat: hit.lat, lng: hit.lng });
                      setPicked(hit);
                      setQ(hit.name);
                    }}
                  >
                    {isSpot(hit) ? `${hit.name} · ${hit.district}` : `${hit.sido} ${hit.name}`}
                  </button>
                </li>
              ))}
            </ul>
          )}
          <div className="filters">
            <button className={colorMode === "활력" ? "on" : ""} onClick={() => setColorMode("활력")}>
              {t("vitalSplit")}
            </button>
            <button className={colorMode === "전력" ? "on" : ""} onClick={() => setColorMode("전력")}>
              {t("powerSplit")}
            </button>
          </div>
          <p className="src">{t("heat")}</p>
          <div className="legend">
            {([1, 2, 3, 4, 5] as VitalityLevel[]).map((lv) => (
              <span key={lv} className="level">
                <span className="dot" style={{ background: LEVELS[lv].color }} />
                {lv} {level(lv)}
              </span>
            ))}
          </div>
          {picked && !isSpot(picked) && (
            <div style={{ marginTop: 10, fontSize: 13 }}>
              <strong>
                {picked.sido} {picked.name}
              </strong>
              <p>
                {t("vitality")} {picked.score}
                {t("score")} <LevelPill level={picked.vitalRank} /> · {t("national")} {picked.vitalRank} {t("quintile")}
              </p>
              <p>
                {t("commercial")} {picked.gwh} GWh · {picked.rankLevel} {t("quintile")}
              </p>
            </div>
          )}
          {picked && isSpot(picked) && (
            <div style={{ marginTop: 10, fontSize: 13 }}>
              <strong>{picked.name}</strong>
              <p>
                {picked.district} {t("basis")}
              </p>
            </div>
          )}
        </div>
        {geo && (
          <MapContainer
            center={[36.4, 127.8]}
            zoom={7}
            zoomSnap={0.5}
            zoomDelta={0.5}
            wheelPxPerZoomLevel={160}
            preferCanvas
            zoomAnimation={false}
            fadeAnimation={false}
            markerZoomAnimation={false}
            style={{ height: "100%", width: "100%" }}
          >
            <TileLayer attribution="&copy; OpenStreetMap" url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
            <RememberZoom zoomRef={zoomRef} />
            <ZoomPaint colorMode={colorMode} sidoRank={sidoRank} sidoPower={sidoPower} stroke={stroke} />
            {focus && <FlyTo lat={focus.lat} lng={focus.lng} />}
            <GeoJSON
              key={`${colorMode}-${theme}-${lang}`}
              data={geo as GeoJsonObject}
              style={(feat) => {
                const row = asNation(feat?.properties);
                const wide = zoomRef.current < 8;
                const level = wide
                  ? ((colorMode === "전력" ? sidoPower : sidoRank).get(row.sido) ?? 3)
                  : colorMode === "전력"
                    ? row.rankLevel
                    : row.vitalRank;
                return {
                  color: stroke,
                  weight: 1.15,
                  opacity: 0.45,
                  fillColor: LEVELS[level].color,
                  fillOpacity: 0.18,
                };
              }}
              onEachFeature={(feat: Feature, layerEl) => {
                const row = asNation(feat.properties);
                layerEl.on("click", () => setPicked(row));
                const tag = row.salesKind === "실측" ? t("measured") : t("inferred");
                layerEl.bindPopup(
                  `<strong>${row.sido} ${row.name}</strong><br/>${t("vitality")} ${row.score}${t("score")}<br/>${t("commercial")} ${row.gwh} GWh<br/>${tag}`,
                );
              }}
            />
            <StreetHeat />
            <MarkTarget key={`${colorMode}-${theme}-${lang}`} sido={targetSido} name={targetName} color={markColor} />
          </MapContainer>
        )}
      </div>
    </div>
  );
}
