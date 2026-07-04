import { apiGet } from './utils.js';

let canvas, ctx;
let nodes = [];
let links = [];
let draggingNode = null;
let selectedNode = null;
let transform = { x: 0, y: 0, zoom: 1 };
let isPanning = false;
let panStart = { x: 0, y: 0 };
let whiteSpotsHighlighted = false;
let animationId = null;

export function initGraph() {
    canvas = document.getElementById('causal-graph-canvas');
    if (!canvas) return;
    
    const rect = canvas.parentElement.getBoundingClientRect();
    canvas.width = rect.width;
    canvas.height = rect.height;
    
    ctx = canvas.getContext('2d');
    
    Promise.all([apiGet('graph/nodes/'), apiGet('graph/edges/')])
        .then(([nodesData, edgesData]) => {
            nodes = nodesData.map(n => ({
                id: n.node_id,
                label: n.label,
                type: n.node_type,
                desc: n.description,
                x: Math.random() * (canvas.width || 400) * 0.8 + 50,
                y: Math.random() * (canvas.height || 300) * 0.8 + 50,
                vx: 0,
                vy: 0,
                radius: 12
            }));
            links = edgesData.map(e => ({
                source: e.source_id,
                target: e.target_id,
                type: e.relation_type,
                color: e.color,
                dash: e.is_dashed
            }));
            if (animationId) cancelAnimationFrame(animationId);
            physicsTick();
        })
        .catch(err => console.error('Graph data load error:', err));
        
    canvas.removeEventListener('mousedown', handleMouseDown);
    canvas.removeEventListener('mousemove', handleMouseMove);
    canvas.removeEventListener('mouseup', handleMouseUp);
    canvas.removeEventListener('wheel', handleWheel);
    
    canvas.addEventListener('mousedown', handleMouseDown);
    canvas.addEventListener('mousemove', handleMouseMove);
    canvas.addEventListener('mouseup', handleMouseUp);
    canvas.addEventListener('wheel', handleWheel);
}

function physicsTick() {
    if (!canvas || !ctx) return;
    const repulsion = 0.8;
    const attraction = 0.04;
    const damping = 0.85;
    for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
            let dx = nodes[j].x - nodes[i].x;
            let dy = nodes[j].y - nodes[i].y;
            let dist = Math.sqrt(dx*dx + dy*dy) || 1;
            if (dist < 150) {
                let force = (150 - dist) * repulsion / dist;
                let fx = dx * force * 0.1;
                let fy = dy * force * 0.1;
                if (nodes[i] !== draggingNode) { nodes[i].vx -= fx; nodes[i].vy -= fy; }
                if (nodes[j] !== draggingNode) { nodes[j].vx += fx; nodes[j].vy += fy; }
            }
        }
    }
    links.forEach(link => {
        const s = nodes.find(n => n.id === link.source);
        const t = nodes.find(n => n.id === link.target);
        if (s && t) {
            let dx = t.x - s.x, dy = t.y - s.y;
            let dist = Math.sqrt(dx*dx + dy*dy) || 1;
            let desiredDist = 120;
            let force = (dist - desiredDist) * attraction;
            let fx = (dx/dist) * force, fy = (dy/dist) * force;
            if (s !== draggingNode) { s.vx += fx; s.vy += fy; }
            if (t !== draggingNode) { t.vx -= fx; t.vy -= fy; }
        }
    });
    nodes.forEach(node => {
        if (node !== draggingNode) {
            node.x += node.vx;
            node.y += node.vy;
            node.vx *= damping;
            node.vy *= damping;
        }
    });
    drawGraph();
    animationId = requestAnimationFrame(physicsTick);
}

function drawGraph() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.save();
    ctx.translate(transform.x, transform.y);
    ctx.scale(transform.zoom, transform.zoom);

    links.forEach(link => {
        const s = nodes.find(n => n.id === link.source);
        const t = nodes.find(n => n.id === link.target);
        if (!s || !t) return;
        ctx.beginPath();
        ctx.moveTo(s.x, s.y);
        ctx.lineTo(t.x, t.y);

        if (whiteSpotsHighlighted) {
            if (link.dash) {
                ctx.setLineDash([5, 5]);
                ctx.strokeStyle = '#F59E0B';
                ctx.lineWidth = 3;
            } else {
                ctx.setLineDash([]);
                ctx.strokeStyle = 'rgba(226, 232, 240, 0.2)';
                ctx.lineWidth = 0.5;
            }
        } else {
            if (link.dash) {
                ctx.setLineDash([5, 5]);
                ctx.strokeStyle = '#F59E0B';
            } else {
                ctx.setLineDash([]);
                ctx.strokeStyle = link.color || '#E2E8F0';
            }
            ctx.lineWidth = 1.5;
        }
        ctx.stroke();
        drawArrow(ctx, s.x, s.y, t.x, t.y, 8);
    });

    nodes.forEach(node => {
        ctx.beginPath();
        ctx.arc(node.x, node.y, node.radius, 0, 2 * Math.PI);
        if (node.type === 'kpi') ctx.fillStyle = '#135BEC';
        else if (node.type === 'param') ctx.fillStyle = '#64748B';
        else if (node.type === 'fail') ctx.fillStyle = '#EF4444';
        else ctx.fillStyle = '#10B981';
        ctx.shadowColor = 'rgba(0,0,0,0.05)';
        ctx.shadowBlur = 4;
        ctx.fill();
        if (selectedNode === node) {
            ctx.beginPath();
            ctx.arc(node.x, node.y, node.radius + 5, 0, 2 * Math.PI);
            ctx.strokeStyle = 'rgba(19,91,236,0.3)';
            ctx.lineWidth = 3;
            ctx.stroke();
        }
        ctx.font = '500 11px Inter';
        ctx.fillStyle = '#1F2937';
        ctx.textAlign = 'center';
        ctx.shadowBlur = 0;
        ctx.fillText(node.label, node.x, node.y - 18);
    });
    ctx.restore();
}

function drawArrow(context, fromx, fromy, tox, toy, r) {
    let angle = Math.atan2(toy - fromy, tox - fromx);
    let x_center = tox - (14 * Math.cos(angle));
    let y_center = toy - (14 * Math.sin(angle));
    context.beginPath();
    context.moveTo(x_center, y_center);
    context.lineTo(x_center - r * Math.cos(angle - Math.PI/6), y_center - r * Math.sin(angle - Math.PI/6));
    context.lineTo(x_center - r * Math.cos(angle + Math.PI/6), y_center - r * Math.sin(angle + Math.PI/6));
    context.closePath();
    context.fillStyle = context.strokeStyle;
    context.fill();
}

function handleMouseDown(e) {
    const rect = canvas.getBoundingClientRect();
    const mouseX = (e.clientX - rect.left - transform.x) / transform.zoom;
    const mouseY = (e.clientY - rect.top - transform.y) / transform.zoom;
    draggingNode = nodes.find(n => Math.hypot(n.x - mouseX, n.y - mouseY) < n.radius + 8);
    if (draggingNode) {
        selectedNode = draggingNode;
        showNodeDetails(draggingNode);
    } else {
        isPanning = true;
        panStart.x = e.clientX - transform.x;
        panStart.y = e.clientY - transform.y;
    }
}

function handleMouseMove(e) {
    if (draggingNode) {
        const rect = canvas.getBoundingClientRect();
        draggingNode.x = (e.clientX - rect.left - transform.x) / transform.zoom;
        draggingNode.y = (e.clientY - rect.top - transform.y) / transform.zoom;
    } else if (isPanning) {
        transform.x = e.clientX - panStart.x;
        transform.y = e.clientY - panStart.y;
    }
}

function handleMouseUp() { draggingNode = null; isPanning = false; }

function handleWheel(e) {
    e.preventDefault();
    const zoomIntensity = 0.05;
    const mouseX = e.clientX - canvas.getBoundingClientRect().left;
    const mouseY = e.clientY - canvas.getBoundingClientRect().top;
    const factor = e.deltaY < 0 ? (1 + zoomIntensity) : (1 - zoomIntensity);
    transform.x = mouseX - (mouseX - transform.x) * factor;
    transform.y = mouseY - (mouseY - transform.y) * factor;
    transform.zoom *= factor;
}

function showNodeDetails(node) {
    const pane = document.getElementById('graph-node-details');
    if (!pane) return;
    pane.classList.remove('hidden');
    document.getElementById('graph-node-title').innerText = node.label;
    document.getElementById('graph-node-desc').innerText = node.desc || 'Параметр системы';
    const typeLabels = { param: 'Параметр', kpi: 'KPI', fail: 'Деградация', mech: 'Механизм' };
    document.getElementById('graph-node-type').innerText = typeLabels[node.type] || 'Сущность';
    const evPane = document.getElementById('graph-node-evidence');
    evPane.innerHTML = '';
    links.filter(l => l.source === node.id || l.target === node.id).forEach(r => {
        const s = nodes.find(n => n.id === r.source);
        const t = nodes.find(n => n.id === r.target);
        evPane.innerHTML += `
            <div class="p-1.5 bg-slate-50 border border-slate-100 rounded text-[10px]">
                <strong>Связь:</strong> ${s?.label} -> <em>${r.type}</em> -> ${t?.label}
            </div>
        `;
    });
}

window.highlightWhiteSpots = function() {
    whiteSpotsHighlighted = !whiteSpotsHighlighted;
    window.showToast(whiteSpotsHighlighted ? 'Белые пятна подсвечены' : 'Режим отключён', 'info');
};

window.resetGraphPhysics = function() {
    nodes.forEach(n => { n.x = Math.random()*(canvas.width || 400)*0.8+50; n.y = Math.random()*(canvas.height || 300)*0.8+50; n.vx=0; n.vy=0; });
    window.showToast('Физика сброшена', 'info');
};

window.handleGraphSearch = function() {
    const query = document.getElementById('graph-search')?.value?.toLowerCase();
    if (!query || query.length < 2) return;
    const found = nodes.find(n => n.label.toLowerCase().includes(query));
    if (found) {
        selectedNode = found;
        transform.x = canvas.width/2 - found.x * transform.zoom;
        transform.y = canvas.height/2 - found.y * transform.zoom;
        showNodeDetails(found);
    }
};

window.closeGraphNodeDetails = function() {
    document.getElementById('graph-node-details')?.classList.add('hidden');
    selectedNode = null;
};