"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

const fallbackLocation = {
  latitude: 12.9716,
  longitude: 77.5946,
  accuracy: null,
  source: "manual",
};

function toNumber(value, fallback) {
  const next = Number(value);
  return Number.isFinite(next) ? next : fallback;
}

export default function IssueLocationPicker({ value, onChange }) {
  const mapRef = useRef(null);
  const mapContainerRef = useRef(null);
  const markerRef = useRef(null);
  const leafletRef = useRef(null);
  const [mapError, setMapError] = useState("");

  const location = useMemo(
    () => ({
      ...fallbackLocation,
      ...value,
      latitude: toNumber(value?.latitude, fallbackLocation.latitude),
      longitude: toNumber(value?.longitude, fallbackLocation.longitude),
    }),
    [value],
  );

  const updateLocation = useCallback(
    (next) => {
    onChange({
      ...location,
      ...next,
    });
    },
    [location, onChange],
  );

  useEffect(() => {
    let canceled = false;

    async function initMap() {
      if (!mapContainerRef.current || mapRef.current) return;

      try {
        const mod = await import("leaflet");
        const L = mod.default || mod;
        leafletRef.current = L;

        const icon = new L.Icon({
          iconUrl:
            "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
          iconRetinaUrl:
            "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
          shadowUrl:
            "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
          iconSize: [25, 41],
          iconAnchor: [12, 41],
        });

        const map = L.map(mapContainerRef.current).setView(
          [location.latitude, location.longitude],
          14,
        );

        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
          attribution: "&copy; OpenStreetMap contributors",
        }).addTo(map);

        const marker = L.marker([location.latitude, location.longitude], {
          draggable: true,
          icon,
        }).addTo(map);

        marker.on("dragend", () => {
          const pos = marker.getLatLng();
          updateLocation({
            latitude: Number(pos.lat.toFixed(6)),
            longitude: Number(pos.lng.toFixed(6)),
            source: "drag",
            accuracy: null,
          });
        });

        map.on("click", (event) => {
          const { lat, lng } = event.latlng;
          marker.setLatLng([lat, lng]);
          updateLocation({
            latitude: Number(lat.toFixed(6)),
            longitude: Number(lng.toFixed(6)),
            source: "map_click",
            accuracy: null,
          });
        });

        if (canceled) {
          map.remove();
          return;
        }

        mapRef.current = map;
        markerRef.current = marker;
      } catch (error) {
        setMapError(error?.message || "Could not load map");
      }
    }

    initMap();

    return () => {
      canceled = true;
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
      markerRef.current = null;
      leafletRef.current = null;
    };
  }, [location.latitude, location.longitude, updateLocation]);

  useEffect(() => {
    const map = mapRef.current;
    const marker = markerRef.current;
    if (!map || !marker) return;

    marker.setLatLng([location.latitude, location.longitude]);
    map.panTo([location.latitude, location.longitude], { animate: true });
  }, [location.latitude, location.longitude]);

  function detectLocation() {
    setMapError("");
    if (typeof window === "undefined" || !navigator.geolocation) {
      setMapError("Geolocation is not available in this browser.");
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const next = {
          latitude: Number(pos.coords.latitude.toFixed(6)),
          longitude: Number(pos.coords.longitude.toFixed(6)),
          accuracy: Number(pos.coords.accuracy.toFixed(2)),
          source: "gps",
        };

        const marker = markerRef.current;
        const map = mapRef.current;
        if (marker && map) {
          marker.setLatLng([next.latitude, next.longitude]);
          map.setView([next.latitude, next.longitude], 16);
        }

        updateLocation(next);
      },
      () => {
        setMapError(
          "Could not detect location. Allow location permission or set pin manually.",
        );
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 },
    );
  }

  return (
    <div className="location-picker">
      <div className="location-picker-header">
        <p className="metric-title">Issue Location</p>
        <button type="button" onClick={detectLocation}>
          Detect My Location
        </button>
      </div>

      <p className="location-helper">
        Tap map or drag marker to correct the issue location before submitting.
      </p>

      <div ref={mapContainerRef} className="map-canvas" />

      <div className="location-grid">
        <label>
          Latitude
          <input
            type="number"
            step="0.000001"
            value={location.latitude}
            onChange={(event) =>
              updateLocation({
                latitude: toNumber(event.target.value, location.latitude),
                source: "manual",
              })
            }
          />
        </label>
        <label>
          Longitude
          <input
            type="number"
            step="0.000001"
            value={location.longitude}
            onChange={(event) =>
              updateLocation({
                longitude: toNumber(event.target.value, location.longitude),
                source: "manual",
              })
            }
          />
        </label>
      </div>

      <p className="location-helper">
        Source: {location.source || "manual"}
        {location.accuracy ? ` | Accuracy: ${location.accuracy}m` : ""}
      </p>

      {mapError && <p className="error">{mapError}</p>}
    </div>
  );
}
