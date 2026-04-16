"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

const fallbackLocation = {
  latitude: 22.5937,
  longitude: 78.9629,
  accuracy: null,
  source: "pending",
};

function toNumber(value, fallback) {
  const next = Number(value);
  return Number.isFinite(next) ? next : fallback;
}

function describeError(error) {
  if (error?.code === 1) {
    return {
      state: "denied",
      message:
        "Location permission denied. Enable browser location permission, or set the pin manually.",
    };
  }
  if (error?.code === 2) {
    return {
      state: "unavailable",
      message:
        "Location unavailable. Check GPS/network and retry, or place the pin manually.",
    };
  }
  if (error?.code === 3) {
    return {
      state: "timeout",
      message:
        "Location request timed out. Retrying with a faster low-accuracy lookup...",
    };
  }
  return {
    state: "unavailable",
    message: "Could not detect location. Place the pin manually to continue.",
  };
}

export default function IssueLocationPicker({ value, onChange }) {
  const mapRef = useRef(null);
  const mapContainerRef = useRef(null);
  const markerRef = useRef(null);
  const locationRef = useRef(fallbackLocation);
  const [statusText, setStatusText] = useState(
    "Tip: use Detect My Location, then drag pin for precise correction.",
  );
  const [detectState, setDetectState] = useState("idle");
  const [detecting, setDetecting] = useState(false);

  const location = useMemo(
    () => ({
      ...fallbackLocation,
      ...value,
      latitude: toNumber(value?.latitude, fallbackLocation.latitude),
      longitude: toNumber(value?.longitude, fallbackLocation.longitude),
    }),
    [value],
  );

  useEffect(() => {
    locationRef.current = location;
  }, [location]);

  const updateLocation = useCallback(
    (next) => {
      onChange({
        ...locationRef.current,
        ...next,
      });
    },
    [onChange],
  );

  useEffect(() => {
    let canceled = false;

    async function initMap() {
      if (!mapContainerRef.current || mapRef.current) return;

      try {
        const mod = await import("leaflet");
        const L = mod.default || mod;

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

        const initial = locationRef.current;

        const map = L.map(mapContainerRef.current).setView(
          [initial.latitude, initial.longitude],
          5,
        );

        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
          attribution: "&copy; OpenStreetMap contributors",
        }).addTo(map);

        const marker = L.marker([initial.latitude, initial.longitude], {
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
          setDetectState("manual");
          setStatusText("Pin moved manually. Location is ready for submission.");
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
          setDetectState("manual");
          setStatusText("Location updated from map click.");
        });

        if (canceled) {
          map.remove();
          return;
        }

        mapRef.current = map;
        markerRef.current = marker;
      } catch (error) {
        setDetectState("error");
        setStatusText(error?.message || "Could not load map");
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
    };
  }, [updateLocation]);

  useEffect(() => {
    const map = mapRef.current;
    const marker = markerRef.current;
    if (!map || !marker) return;

    marker.setLatLng([location.latitude, location.longitude]);
    map.panTo([location.latitude, location.longitude], { animate: true });
  }, [location.latitude, location.longitude]);

  const detectLocation = useCallback(() => {
    if (typeof window !== "undefined" && !window.isSecureContext) {
      setDetectState("insecure");
      setStatusText(
        "Location requires HTTPS (or localhost). Open this app from a secure URL.",
      );
      return;
    }

    if (typeof window === "undefined" || !navigator.geolocation) {
      setDetectState("unsupported");
      setStatusText("Geolocation is not available in this browser.");
      return;
    }

    setDetectState("detecting");
    setStatusText("Detecting your location...");
    setDetecting(true);

    const requestPosition = (options) =>
      new Promise((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(resolve, reject, options);
      });

    const setDetected = (pos, source) => {
      const next = {
        latitude: Number(pos.coords.latitude.toFixed(6)),
        longitude: Number(pos.coords.longitude.toFixed(6)),
        accuracy: Number(pos.coords.accuracy.toFixed(2)),
        source,
      };

      const marker = markerRef.current;
      const map = mapRef.current;
      if (marker && map) {
        marker.setLatLng([next.latitude, next.longitude]);
        map.setView([next.latitude, next.longitude], 16);
      }

      updateLocation(next);
      setDetectState("success");
      setStatusText(
        `Detected: ${next.latitude}, ${next.longitude} (accuracy ${next.accuracy}m). You can still drag pin to fine-tune.`,
      );
      setDetecting(false);
    };

    requestPosition({ enableHighAccuracy: true, timeout: 12000, maximumAge: 0 })
      .then((pos) => setDetected(pos, "gps"))
      .catch((error) => {
        const first = describeError(error);
        setDetectState(first.state);
        setStatusText(first.message);

        if (error?.code !== 2 && error?.code !== 3) {
          setDetecting(false);
          return;
        }

        requestPosition({
          enableHighAccuracy: false,
          timeout: 8000,
          maximumAge: 120000,
        })
          .then((pos) => setDetected(pos, "gps_fallback"))
          .catch((retryError) => {
            const retry = describeError(retryError);
            setDetectState(retry.state);
            if (retryError?.code === 3) {
              setStatusText(
                "Location still timed out. Please place the pin manually.",
              );
            } else {
              setStatusText(retry.message);
            }
            setDetecting(false);
          });
      });
  }, [updateLocation]);

  useEffect(() => {
    let active = true;

    async function maybeAutoDetect() {
      if (
        typeof navigator === "undefined" ||
        !navigator.permissions ||
        !navigator.geolocation
      ) {
        return;
      }

      try {
        const permission = await navigator.permissions.query({
          name: "geolocation",
        });
        if (!active) return;

        if (permission.state === "granted") {
          setStatusText("Location permission granted. Auto-detecting...");
          detectLocation();
        } else if (permission.state === "denied") {
          setDetectState("denied");
          setStatusText(
            "Location permission is blocked in browser settings. Use manual pin placement or enable permission and retry.",
          );
        } else {
          setStatusText(
            "Allow location access for auto-detect, or place your pin manually.",
          );
        }
      } catch {
        setStatusText("Use Detect My Location, or place your pin manually.");
      }
    }

    maybeAutoDetect();

    return () => {
      active = false;
    };
  }, [detectLocation]);

  return (
    <div className="location-picker">
      <div className="location-picker-header">
        <p className="metric-title">Issue Location</p>
        <button type="button" onClick={detectLocation} disabled={detecting}>
          {detecting
            ? "Detecting..."
            : detectState === "success"
              ? "Detect Again"
              : "Detect My Location"}
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
                accuracy: null,
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
                accuracy: null,
              })
            }
          />
        </label>
      </div>

      <p className="location-helper">
        Source: {location.source || "manual"}
        {location.accuracy ? ` | Accuracy: ${location.accuracy}m` : ""}
      </p>

      {statusText && (
        <p
          className={
            detectState === "success"
              ? "notice"
              : detectState === "idle" || detectState === "detecting"
                ? "location-helper"
                : "error"
          }
        >
          {statusText}
        </p>
      )}
    </div>
  );
}
