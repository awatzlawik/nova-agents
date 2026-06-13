# NOVA — Memory-/Persistenz-Konvention (Invariante 4/7)

> Eigendefinition (BMAD-Sidecar ist in V4 NICHT real — phase0/02). Datei-Layout nach NovelWriter
> (`consistency_*.json`, `checkpoint_state.json`), Memory-Trennung nach RecurrentGPT (short/long).
> Retrieval-/Vektor-Mechanik ist **deferred bis Phase 2** (Struktur hält Platz frei).

## Layout pro Autorprojekt

```
projects/<projekt>/_memory/
  sidecars/<skill-id>/state.json   # per-Persona persistenter Zustand (cross-session)
  story-bible/                     # SSoT-Shards = Instanzen der nova/templates (versioniert)
  continuity/
    characters.json                # CHAR-Faktenregister  (Schema: NovelWriter CharacterState)
    world.json                     # WORLD-Fakten
    plots.json                     # Plot-Threads
  summaries/                       # Szenen-Summaries (RecurrentGPT short-memory) — ab Phase 2
  index/                           # Saliency-/Retrieval-Index — ab Phase 2 (Vektor deferred)
  gates/checkpoint_state.json      # Phasen-Gating + user_approved (Invariante 7)
```

## Prinzipien
- **SSoT:** Die Story Bible (`story-bible/`) ist alleinige Wahrheitsquelle; alles andere ist abgeleitet.
- **Sharding + Token-Budget (Invariante 4):** Personas laden nur eigene Dependencies, geshardet.
- **IDs:** `continuity/*.json` referenziert die Bible-IDs (CHAR-/WORLD-/SCENE-…) aus `naming.md`.
- **Gating (Invariante 7):** `checkpoint_state.json` hält Phase-Status + `user_approved` (Annehmen-Gate);
  Folgephasen bauen nur auf freigegebenen Artefakten auf.

## checkpoint_state.json (Minimal-Schema)
```json
{
  "project": "<name>",
  "current_phase": 0,
  "phases": {
    "0": { "status": "in_progress|done", "user_approved": false, "artifacts": [] }
  }
}
```

## Phasen-Bezug
- Phase 0: Ordnerkonvention + leere Struktur + `checkpoint_state.json` (kein Retrieval-Code).
- Phase 1: `story-bible/`-Instanzen + `continuity/`-Befüllung.
- Phase 2: `summaries/` + `index/` (RecurrentGPT/Retrieval) aktiv.
