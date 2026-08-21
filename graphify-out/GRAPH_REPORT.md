# Graph Report - frontend/src  (2026-08-21)

## Corpus Check
- Corpus is ~5,802 words - fits in a single context window. You may not need a graph.

## Summary
- 69 nodes · 67 edges · 5 communities detected
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 4 edges (avg confidence: 0.8)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]

## God Nodes (most connected - your core abstractions)
1. `get()` - 12 edges
2. `route()` - 9 edges
3. `kecTier()` - 4 edges
4. `screenFromHash()` - 2 edges
5. `onHashChange()` - 2 edges
6. `fireTierClass()` - 2 edges
7. `landslideTierClass()` - 2 edges
8. `useDashboard()` - 2 edges
9. `fireSummary()` - 2 edges
10. `fireGrid()` - 2 edges

## Surprising Connections (you probably didn't know these)
- `route()` --calls--> `get()`  [INFERRED]
  /home/jthe/Dev/localgit/mata_api/frontend/src/api/mockFetch.ts → /home/jthe/Dev/localgit/mata_api/frontend/src/api/client.ts
- `kecTier()` --calls--> `fireTierClass()`  [INFERRED]
  /home/jthe/Dev/localgit/mata_api/frontend/src/components/MapView.tsx → /home/jthe/Dev/localgit/mata_api/frontend/src/types.ts
- `kecTier()` --calls--> `landslideTierClass()`  [INFERRED]
  /home/jthe/Dev/localgit/mata_api/frontend/src/components/MapView.tsx → /home/jthe/Dev/localgit/mata_api/frontend/src/types.ts
- `AlertPanel()` --calls--> `useDashboard()`  [INFERRED]
  /home/jthe/Dev/localgit/mata_api/frontend/src/components/AlertPanel.tsx → /home/jthe/Dev/localgit/mata_api/frontend/src/screens/dashboard-context.ts

## Communities

### Community 0 - "Community 0"
Cohesion: 0.25
Nodes (12): ConnectionError, get(), getAlerts(), getBoundaries(), getFireCell(), getFireGrid(), getFireOverlay(), getFireSummary() (+4 more)

### Community 1 - "Community 1"
Cohesion: 0.36
Nodes (8): alerts(), fireCell(), fireGrid(), fireSummary(), landslideGrid(), landslideSummary(), respond(), route()

### Community 2 - "Community 2"
Cohesion: 0.32
Nodes (4): kecStyle(), kecTier(), fireTierClass(), landslideTierClass()

### Community 4 - "Community 4"
Cohesion: 0.5
Nodes (2): AlertPanel(), useDashboard()

### Community 5 - "Community 5"
Cohesion: 1.0
Nodes (2): onHashChange(), screenFromHash()

## Knowledge Gaps
- **Thin community `Community 4`** (4 nodes): `AlertPanel()`, `AlertPanel.tsx`, `useDashboard()`, `dashboard-context.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 5`** (3 nodes): `onHashChange()`, `screenFromHash()`, `App.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get()` connect `Community 0` to `Community 1`?**
  _High betweenness centrality (0.067) - this node is a cross-community bridge._
- **Why does `route()` connect `Community 1` to `Community 0`?**
  _High betweenness centrality (0.060) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `kecTier()` (e.g. with `fireTierClass()` and `landslideTierClass()`) actually correct?**
  _`kecTier()` has 2 INFERRED edges - model-reasoned connections that need verification._