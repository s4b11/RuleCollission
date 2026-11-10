type Node = { id: string; name: string; office: string; row: number; state: string; goal: boolean }
type Edge = { from: string; to: string }
export type Graph = { nodes: Node[]; edges: Edge[] }

const WIDTH = 196
const HEIGHT = 52
const GAP_X = 36
const GAP_Y = 34

const COLOURS: Record<string, { fill: string; stroke: string }> = {
  held: { fill: '#ecfdf5', stroke: '#34d399' },
  route: { fill: '#eef3fd', stroke: '#2f5fd0' },
  blocked: { fill: '#fef2f2', stroke: '#f87171' },
  pending: { fill: '#ffffff', stroke: '#d0d5dd' },
}

const LEGEND = [
  ['held', 'On file'],
  ['route', 'Next steps'],
  ['blocked', 'Waiting on each other'],
  ['pending', 'Not reachable yet'],
]

const shorten = (text: string, length: number) => (text.length > length ? text.slice(0, length - 1) + '…' : text)

export default function CaseGraph({ graph }: { graph: Graph }) {
  const rows: Node[][] = []
  for (const node of graph.nodes) (rows[node.row] ??= []).push(node)
  const widest = Math.max(...rows.map((row) => row.length))
  const fullWidth = widest * (WIDTH + GAP_X)

  const position: Record<string, { x: number; y: number }> = {}
  rows.forEach((row, rowIndex) => {
    const indent = (fullWidth - row.length * (WIDTH + GAP_X)) / 2
    row.forEach((node, index) => {
      position[node.id] = { x: indent + index * (WIDTH + GAP_X) + GAP_X / 2, y: rowIndex * (HEIGHT + GAP_Y) + 4 }
    })
  })
  const state = Object.fromEntries(graph.nodes.map((n) => [n.id, n.state]))

  function path(edge: Edge) {
    const a = position[edge.from]
    const b = position[edge.to]
    if (a.y === b.y) {
      const leftToRight = a.x < b.x
      const y = a.y + HEIGHT / 2 + (leftToRight ? -9 : 9)
      return leftToRight ? `M${a.x + WIDTH},${y} L${b.x},${y}` : `M${a.x},${y} L${b.x + WIDTH},${y}`
    }
    const startX = a.x + WIDTH / 2
    const startY = a.y + HEIGHT
    const endX = b.x + WIDTH / 2
    const middle = (startY + b.y) / 2
    return `M${startX},${startY} C${startX},${middle} ${endX},${middle} ${endX},${b.y}`
  }

  return (
    <div>
      <div className="overflow-x-auto">
        <svg width={fullWidth} height={rows.length * (HEIGHT + GAP_Y)} className="mx-auto">
          <defs>
            <marker id="arrow" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7" markerHeight="7" orient="auto">
              <path d="M0,0 L8,4 L0,8 z" fill="#94a3b8" />
            </marker>
            <marker id="arrow-stuck" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7" markerHeight="7" orient="auto">
              <path d="M0,0 L8,4 L0,8 z" fill="#dc2626" />
            </marker>
          </defs>
          {graph.edges.map((edge) => {
            const stuck = state[edge.from] === 'blocked' && state[edge.to] === 'blocked'
            return (
              <path key={edge.from + edge.to} d={path(edge)} fill="none"
                markerEnd={stuck ? 'url(#arrow-stuck)' : 'url(#arrow)'}
                stroke={stuck ? '#dc2626' : '#94a3b8'} strokeWidth={stuck ? 1.6 : 1.2} />
            )
          })}
          {graph.nodes.map((node) => {
            const { x, y } = position[node.id]
            const colour = COLOURS[node.state]
            return (
              <g key={node.id}>
                <rect x={x} y={y} width={WIDTH} height={HEIGHT} rx={10} fill={colour.fill} stroke={colour.stroke}
                  strokeWidth={node.goal ? 2.5 : 1.3} />
                <text x={x + 12} y={y + 22} fontSize="12.5" fontWeight="600" fill="#101828">{shorten(node.name, 27)}</text>
                <text x={x + 12} y={y + 39} fontSize="11" fill="#667085">
                  {node.goal ? 'Goal · ' : ''}{shorten(node.office, node.goal ? 20 : 28)}
                </text>
              </g>
            )
          })}
        </svg>
      </div>
      <div className="mt-4 flex flex-wrap items-center gap-2 text-xs text-muted">
        {LEGEND.map(([key, label]) => (
          <span key={key} className="flex items-center gap-1.5 rounded-full border border-line px-2.5 py-1">
            <span className="inline-block h-2.5 w-2.5 rounded-full border"
              style={{ background: COLOURS[key].fill, borderColor: COLOURS[key].stroke }} />
            {label}
          </span>
        ))}
        <span className="ml-1">An arrow means "is needed before".</span>
      </div>
    </div>
  )
}
