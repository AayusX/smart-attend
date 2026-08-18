import numpy as np
from typing import Dict, List, Optional, Tuple
from collections import defaultdict, deque
from dataclasses import dataclass, field
import time
import logging

logger = logging.getLogger(__name__)


@dataclass
class Track:
    track_id: int
    bbox: Tuple[int, int, int, int]
    embedding: Optional[np.ndarray] = None
    student_id: Optional[int] = None
    student_name: Optional[str] = None
    confidence: float = 0.0
    is_live: bool = False
    liveness_score: float = 0.0
    recognition_buffer: deque = field(default_factory=lambda: deque(maxlen=7))
    position_history: deque = field(default_factory=lambda: deque(maxlen=30))
    frames_tracked: int = 0
    last_recognition_frame: int = 0
    needs_recognition: bool = True
    is_verified: bool = False
    stable_count: int = 0
    first_seen: float = field(default_factory=time.time)

    @property
    def center(self) -> Tuple[int, int]:
        x1, y1, x2, y2 = self.bbox
        return ((x1 + x2) // 2, (y1 + y2) // 2)

    @property
    def stable_identity(self) -> Optional[int]:
        if len(self.recognition_buffer) < 3:
            return None
        counts = defaultdict(int)
        for sid, _ in self.recognition_buffer:
            if sid is not None:
                counts[sid] += 1
        if not counts:
            return None
        best_id = max(counts, key=counts.get)
        if counts[best_id] >= 3:
            return best_id
        return None

    def add_recognition(self, student_id: Optional[int], confidence: float):
        self.recognition_buffer.append((student_id, confidence))
        self.last_recognition_frame = time.time()


class CentroidTracker:
    def __init__(self, max_disappeared: int = 15, max_distance: int = 100):
        self.next_track_id = 0
        self.tracks: Dict[int, Track] = {}
        self.disappeared: Dict[int, int] = defaultdict(int)
        self.max_disappeared = max_disappeared
        self.max_distance = max_distance

    def update(self, detections: List[Tuple[int, int, int, int]],
               embeddings: Optional[List[np.ndarray]] = None) -> List[Track]:
        if len(detections) == 0:
            for track_id in list(self.disappeared.keys()):
                self.disappeared[track_id] += 1
                if self.disappeared[track_id] > self.max_disappeared:
                    self.deregister(track_id)
            return list(self.tracks.values())

        centroids = []
        for bbox in detections:
            x1, y1, x2, y2 = bbox
            centroids.append(((x1 + x2) // 2, (y1 + y2) // 2))

        if len(self.tracks) == 0:
            for i, (centroid, bbox) in enumerate(zip(centroids, detections)):
                embedding = embeddings[i] if embeddings and i < len(embeddings) else None
                self.register(bbox, embedding)
            return list(self.tracks.values())

        track_ids = list(self.tracks.keys())
        track_centroids = [self.tracks[tid].center for tid in track_ids]
        D = self._distance_matrix(track_centroids, centroids)
        matched, unmatched_tracks, unmatched_detections = self._match(D)

        for track_idx, detection_idx in matched:
            track_id = track_ids[track_idx]
            self.tracks[track_id].bbox = detections[detection_idx]
            self.tracks[track_id].frames_tracked += 1
            self.tracks[track_id].position_history.append(centroids[detection_idx])
            if embeddings and detection_idx < len(embeddings):
                self.tracks[track_id].embedding = embeddings[detection_idx]
            self.disappeared[track_id] = 0

        for track_idx in unmatched_tracks:
            track_id = track_ids[track_idx]
            self.disappeared[track_id] += 1
            if self.disappeared[track_id] > self.max_disappeared:
                self.deregister(track_id)

        for detection_idx in unmatched_detections:
            embedding = embeddings[detection_idx] if embeddings and detection_idx < len(embeddings) else None
            self.register(detections[detection_idx], embedding)

        return list(self.tracks.values())

    def register(self, bbox, embedding=None):
        track = Track(
            track_id=self.next_track_id,
            bbox=bbox,
            embedding=embedding,
        )
        self.tracks[self.next_track_id] = track
        self.next_track_id += 1

    def deregister(self, track_id: int):
        self.tracks.pop(track_id, None)
        self.disappeared.pop(track_id, None)

    def _distance_matrix(self, tc, dc):
        D = np.zeros((len(tc), len(dc)))
        for i, a in enumerate(tc):
            for j, b in enumerate(dc):
                D[i, j] = ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5
        return D

    def _match(self, D):
        matched = []
        unmatched_tracks = list(range(D.shape[0]))
        unmatched_detections = list(range(D.shape[1]))

        if D.size == 0:
            return matched, unmatched_tracks, unmatched_detections

        while len(unmatched_tracks) > 0 and len(unmatched_detections) > 0:
            min_idx = np.unravel_index(np.argmin(D), D.shape)
            ti, di = min_idx
            if D[ti, di] > self.max_distance:
                break
            matched.append((ti, di))
            unmatched_tracks.remove(ti)
            unmatched_detections.remove(di)
            D[ti, :] = np.inf
            D[:, di] = np.inf

        return matched, unmatched_tracks, unmatched_detections

    def clear(self):
        self.tracks.clear()
        self.disappeared.clear()
        self.next_track_id = 0
