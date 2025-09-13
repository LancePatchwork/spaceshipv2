# M12 — UI Architecture (Widget‑Driven Windows) v0

Status: Frozen
Owner: UI/Frontend

Goal: Every screen is a *container* of widgets. Containers hold only layout (tiles). All behavior/data lives in backend **widgets** (registry + instances).

## Core types
```ts
export type WidgetId = string;
export type WidgetCtx = {
  srs: SRSState;
  flows: Flow[];
  crew: Crew[];
  postOrder: (o: EventOrder) => void;
  setPrefill: (o: EventOrder|null) => void;
};

export type WidgetDef<P=any> = {
  id: WidgetId;
  name: string;
  defaultProps: P;
  render: (ctx: WidgetCtx, inst: WidgetInstance<P>) => React.ReactNode;
  actions?: ActionDef<P>[];
};

export type WidgetInstance<P=any> = {
  instId: string;
  widgetId: WidgetId;
  props: P;
};

export type WidgetTile = {
  instId: string; x: number; y: number; w: number; h: number;
  local?: Record<string, unknown>;
};
```

Rules:
1) Only widgets read live game state via `WidgetCtx`.
2) Containers never call systems; they pass `ctx` to widget `render`.
3) Context‑menus come from `WidgetDef.actions`; containers may append generic actions (Remove/Duplicate/Open).

## Registry & Store stubs
```ts
export const WIDGETS: Record<WidgetId, WidgetDef<any>> = {};
export function registerWidget<P>(def: WidgetDef<P>) { WIDGETS[def.id] = def as WidgetDef<any>; }

export type InstanceStore = Record<string, WidgetInstance<any>>;

export function createInstance(store: InstanceStore, set: (s:InstanceStore)=>void, widgetId: WidgetId, props: any) {
  const instId = `w_${Math.random().toString(36).slice(2,7)}`;
  set({ ...store, [instId]: { instId, widgetId, props } });
  return instId;
}
```

## Container window
```tsx
const ContainerWindow: React.FC<{
  tiles: WidgetTile[];
  setTiles: (t:WidgetTile[])=>void;
  instances: InstanceStore;
  ctx: WidgetCtx;
}> = ({ tiles, setTiles, instances, ctx }) => {
  const drag = useRef<null | { id:string; dx:number; dy:number }>(null);
  return (
    <div className="w-full h-full relative"
         onMouseMove={(e)=> drag.current && setTiles(tiles.map(t=> t.instId===drag.current!.id? { ...t, x: e.clientX - drag.current!.dx, y: e.clientY - drag.current!.dy } : t))}
         onMouseUp={()=> drag.current=null}>
      {tiles.map(t=>{
        const inst = instances[t.instId]; const def = WIDGETS[inst?.widgetId]; if(!inst||!def) return null;
        return (
          <div key={t.instId} className="absolute bg-[#181818] border border-[#333]"
               style={{left:t.x, top:t.y, width:t.w, height:t.h}}>
            <div className="h-6 px-2 flex items-center justify-between bg-[#222] text-[11px] cursor-move"
                 onMouseDown={(e)=>{ const r=(e.currentTarget.parentElement as HTMLDivElement).getBoundingClientRect(); drag.current={ id:t.instId, dx:e.clientX-r.left, dy:e.clientY-r.top }; }}>
              <span>{def.name}</span>
            </div>
            <div className="p-2 overflow-auto" style={{height:`calc(100% - 1.5rem)`}}>
              {def.render(ctx, inst)}
            </div>
          </div>
        );
      })}
    </div>
  );
};
```

## Example widgets
```tsx
registerWidget<{ portId?: string}>({
  id:"port_monitor",
  name:"Port Monitor",
  defaultProps:{ portId: undefined },
  render:(ctx, inst)=>{
    const p = ctx.srs.ports.find(pp=>pp.id===inst.props.portId);
    if(!p) return <div className="text-xs text-gray-400">Select a port</div>;
    const total = p.dir==='out'? sumOut(ctx.flows, p.id) : sumIn(ctx.flows, p.id);
    return <div className="text-xs">Port <span className="font-mono">{p.id}</span><div className="mt-1">Current/Cap: <span className="font-mono">{total}/{p.cap}</span></div></div>;
  }
});
```

## Extraction
- Source tables/rows emit drag payloads or provide an *Extract to Widgets* action.
- App ensures a **Widgets** window exists, then adds a tile referencing the new instance.

## Persistence (M11)
```
{
  "ui": {
    "widgets_version": 1,
    "instances": { "w_ab12c": { "widgetId": "port_monitor", "props": {"portId":"reactor.pwr_out"} } },
    "windows": { "srs-1": { "tiles": [{ "instId":"w_ab12c","x":40,"y":40,"w":220,"h":110 }] } }
  }
}
```

## Performance
- Widgets re-render on snapshot identity change only.
- Expensive work off-thread; **atomic publish** snapshot to UI.
- Non-critical panels update async (no main-loop stutter).

## Menu halo
- 10px tolerance around context menus; within halo → fade; beyond → close; `Esc` closes.

## Demo mapping now
- `port_monitor`, `srs_ports_table`, `srs_flows`, `crew_table`(stub), `event_log`(stub).
- Next: `crew_monitor`, `dc_graph`, `dc_list`, `systems_power`, `systems_thermal`, `market_board`.
