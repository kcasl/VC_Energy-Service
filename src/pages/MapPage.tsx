import { useCallback, useEffect, useMemo, useState } from "react";
import { GeoJSON, MapContainer, TileLayer, useMap } from "react-leaflet";
import type { Feature, FeatureCollection, GeoJsonObject } from "geojson";
import "leaflet/dist/leaflet.css";
import LevelPill from "../components/LevelPill";
import { api, type MapSpot } from "../lib/load";
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

type Cell = {
  lat: number;
  lng: number;
  stores: number;
  vitalRank: VitalityLevel;
  sido: string;
  name: string;
  score: number;
  kind: "추론";
};

type Box = { south: number; north: number; west: number; east: number };

function FlyTo({ lat, lng }: { lat: number; lng: number }) {
  const map = useMap();
  useEffect(() => {
    map.flyTo([lat, lng], 12, { duration: 0.7 });
  }, [lat, lng, map]);
  return null;
}

function WatchView({ onView }: { onView: (zoom: number, box: Box) => void }) {
  const map = useMap();
  useEffect(() => {
    const send = () => {
      const box = map.getBounds();
      onView(map.getZoom(), {
        south: box.getSouth(),
        north: box.getNorth(),
        west: box.getWest(),
        east: box.getEast(),
      });
    };
    send();
    map.on("moveend", send);
    return () => {
      map.off("moveend", send);
    };
  }, [map, onView]);
  return null;
}

export default function MapPage() {
  const [spots, setSpots] = useState<MapSpot[]>([]);
  const [geo, setGeo] = useState<FeatureCollection | null>(null);
  const [grid, setGrid] = useState<FeatureCollection | null>(null);
  const [q, setQ] = useState("");
  const [zoom, setZoom] = useState(7);
  const [box, setBox] = useState<Box | null>(null);
  const [colorMode, setColorMode] = useState<"활력" | "전력">("활력");
  const [focus, setFocus] = useState<{ lat: number; lng: number } | null>(null);
  const [picked, setPicked] = useState<Nation | MapSpot | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.map().then((d) => setSpots(d.spots)).catch(() => setError("서버에 연결되지 않습니다."));
    fetch("/data/processed/national_map.geojson?v=vital")
      .then((res) => {
        if (!res.ok) throw new Error(String(res.status));
        return res.json() as Promise<FeatureCollection>;
      })
      .then(setGeo)
      .catch(() => setError("지도를 읽지 못했습니다."));
    fetch("/data/processed/alley_grid.geojson")
      .then((res) => {
        if (!res.ok) throw new Error(String(res.status));
        return res.json() as Promise<FeatureCollection>;
      })
      .then(setGrid)
      .catch(() => setGrid(null));
  }, []);

  const onView = useCallback((nextZoom: number, nextBox: Box) => {
    setZoom(nextZoom);
    setBox(nextBox);
  }, []);
  const grain = zoom < 8 ? "시도" : zoom < 12 ? "시군구" : "골목";

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
  const visibleGrid = useMemo(() => {
    if (!grid || !box || grain !== "골목") return null;
    const features = grid.features.filter((feat) => {
      const cell = feat.properties as Cell;
      return cell.lat >= box.south && cell.lat <= box.north && cell.lng >= box.west && cell.lng <= box.east;
    });
    return { type: "FeatureCollection", features } as FeatureCollection;
  }, [grid, box, grain]);
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
    <div>
      <div className="page-head">
        <div>
          <h1>지도</h1>
          <p>
            축소하면 시도, 보통은 시군구, 확대하면 약 1.5km 칸으로 나뉩니다. 칸 색은 그 시군구 활력을 상가 밀도로 나눈{" "}
            <span className="tag guess">추론</span>입니다. 한전·공동주택·LH 공개분에는 골목 전력이 없습니다.
          </p>
        </div>
      </div>
      <div className="map-wrap">
        <div className="map-panel">
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="수원, 해운대구, 제주" />
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
          <p className="src">지금 칸: {grain}</p>
          <div className="filters">
            <button className={colorMode === "활력" ? "on" : ""} onClick={() => setColorMode("활력")}>
              활력 5등분
            </button>
            <button className={colorMode === "전력" ? "on" : ""} onClick={() => setColorMode("전력")}>
              전력 5등분
            </button>
          </div>
          <div className="legend">
            {([1, 2, 3, 4, 5] as VitalityLevel[]).map((lv) => (
              <span key={lv} className="level">
                <span className="dot" style={{ background: LEVELS[lv].color }} />
                {lv} {LEVELS[lv].label}
              </span>
            ))}
          </div>
          {picked && !isSpot(picked) && (
            <div style={{ marginTop: 10, fontSize: 13 }}>
              <strong>
                {picked.sido} {picked.name}
              </strong>
              <p>
                활력 {picked.score}점 <LevelPill level={picked.vitalRank} /> · 전국 {picked.vitalRank}분위
              </p>
              <p>일반용 {picked.gwh} GWh · 전력 {picked.rankLevel}분위</p>
              {picked.salesKind === "실측" ? (
                <p>매출·유동·개폐업은 실측입니다.</p>
              ) : (
                <p>
                  <span className="tag guess">추론</span> 매출·유동은 상가 수와 점포당 전력으로, 개폐업 자리는 전력 증감으로 넣었습니다.
                </p>
              )}
            </div>
          )}
          {picked && isSpot(picked) && (
            <div style={{ marginTop: 10, fontSize: 13 }}>
              <strong>{picked.name}</strong>
              <p>
                <span className="tag gap">데이터 부족</span> {picked.name}만의 전력은 없습니다. 색은 {picked.district}{" "}
                기준입니다.
              </p>
            </div>
          )}
        </div>
        {geo && (
          <MapContainer center={[36.4, 127.8]} zoom={7} style={{ height: "100%", width: "100%" }}>
            <TileLayer
              attribution="&copy; OpenStreetMap"
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            <WatchView onView={onView} />
            {focus && <FlyTo lat={focus.lat} lng={focus.lng} />}
            {grain !== "골목" && (
              <GeoJSON
                key={`${colorMode}-${grain}`}
                data={geo as GeoJsonObject}
                style={(feat) => {
                  const row = asNation(feat?.properties);
                  const level =
                    grain === "시도"
                      ? ((colorMode === "전력" ? sidoPower : sidoRank).get(row.sido) ?? 3)
                      : colorMode === "전력"
                        ? row.rankLevel
                        : row.vitalRank;
                  return {
                    color: grain === "시도" ? LEVELS[level].color : "#fff",
                    weight: grain === "시도" ? 0.4 : 0.6,
                    fillColor: LEVELS[level].color,
                    fillOpacity: 0.72,
                  };
                }}
                onEachFeature={(feat: Feature, layerEl) => {
                  const row = asNation(feat.properties);
                  layerEl.on("click", () => setPicked(row));
                  const tag = row.salesKind === "실측" ? "매출·유동 실측" : "매출·유동 추론";
                  layerEl.bindPopup(
                    `<strong>${row.sido} ${row.name}</strong><br/>활력 ${row.score}점<br/>일반용 ${row.gwh} GWh<br/>${tag}`,
                  );
                }}
              />
            )}
            {visibleGrid && (
              <GeoJSON
                key={`${visibleGrid.features.length}-${box?.south}`}
                data={visibleGrid as GeoJsonObject}
                style={(feat) => {
                  const cell = feat?.properties as Cell;
                  return {
                    color: "#fff",
                    weight: 0.4,
                    fillColor: LEVELS[cell.vitalRank].color,
                    fillOpacity: 0.78,
                  };
                }}
                onEachFeature={(feat: Feature, layerEl) => {
                  const cell = feat.properties as Cell;
                  layerEl.bindPopup(
                    `<strong>${cell.sido} ${cell.name}</strong><br/>이 칸 상가 ${cell.stores}곳<br/>활력 ${cell.score}점을 밀도로 나눈 추론`,
                  );
                }}
              />
            )}
          </MapContainer>
        )}
      </div>
    </div>
  );
}
