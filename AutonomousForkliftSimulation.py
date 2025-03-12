import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import random

# Node Positions

positions = {
    'p1': np.array([0, 0]), # 1 unit equals 100 meters
    'p2': np.array([5, 0]),
    'p3': np.array([12, 0]),
    'p4': np.array([0, 3]),
    'p5': np.array([5, 6]),
    'p6': np.array([8, -1]),
    'p7': np.array([10, 1])
}

# Forklift Edges - These edges represent the possible paths for each forklift.

forklift_edges = {
    # Blue forklift 1 - p1 <-> p2 <-> p3
    "Forklift 1": [
        ("p1", "p2"),
        ("p2", "p3")
    ],
    # Red forklift 2 - p1 <-> p4, p4 <-> p2, p2 <-> p5
    "Forklift 2": [
        ("p1", "p4"),
        ("p4", "p2"),
        ("p2", "p5")
    ],
    # Green forklift 3- p6 <-> p7
    "Forklift 3": [
        ("p6", "p7")
    ]
}

# Route Pools (Round-Trip Routes for Each Forklift)

routes_pool = {
    # Blue routes
    "Forklift 1": [
        ["p1", "p2", "p3", "p2", "p1"],
        ["p1", "p2", "p3", "p2", "p3", "p2", "p1"]
    ],
    # Red routes
    "Forklift 2": [
        # Ex. 1: Long route that passes p5
        ["p1", "p4", "p2", "p5", "p2", "p4", "p1"],
        # Ex. 2: Shorter route that does not pass p5
        ["p1", "p4", "p2", "p4", "p1"]
    ],
    # Green routes
    "Forklift 3": [
        ["p6", "p7", "p6"],
        ["p6", "p7", "p6", "p7", "p6"]
    ]
}

# select a random route for each forklift.
current_routes = {}
for forklift, pool in routes_pool.items():
    current_routes[forklift] = random.choice(pool)


# Simulation Parameters

max_speed = 3.0        # Max speed (m/s)
acceleration = 1.0     # Acceleration (m/s^2)
load_unload_time = 120 # Waiting time at each stop -seconds
dt = 0.1               # Time step -seconds
total_time = 180       # Total simulation time -seconds
num_frames = int(total_time / dt)


# Compute Segments (Convert a Route into Segments)

def compute_segments(route):
    segments = []
    for i in range(len(route) - 1):
        start_node = route[i]
        end_node = route[i+1]
        start_pos = positions[start_node]
        end_pos = positions[end_node]
        # Distance calculation (1 unit = 100 m)
        distance = np.linalg.norm(end_pos - start_pos) * 100
        segments.append({
            'start': start_pos,
            'end': end_pos,
            'distance_m': distance
        })
    return segments

forklift_segments = {}
for forklift, route in current_routes.items():
    forklift_segments[forklift] = compute_segments(route)


# Drawing with Matplotlib

fig, ax = plt.subplots()
ax.set_aspect('equal')
ax.set_title("Route Optimization of Autonomous Forklift Simulation")

# Set plot limits
all_x = [pos[0] for pos in positions.values()]
all_y = [pos[1] for pos in positions.values()]
ax.set_xlim(min(all_x)-2, max(all_x)+2)
ax.set_ylim(min(all_y)-2, max(all_y)+2)

# Draw nodes and labels
for node, pos in positions.items():
    ax.plot(pos[0], pos[1], 'ko')
    ax.text(pos[0]+0.1, pos[1]+0.1, node, fontsize=9)

# Define forklift colors
colors = {
    "Forklift 1": "blue",
    "Forklift 2": "red",
    "Forklift 3": "green"
}

# -- Draw all possible edges --
# This ensures that even if Forklift 2 doesn't use p2<->p5, the edge is visible.
for forklift, edges in forklift_edges.items():
    c = colors[forklift]
    for (n1, n2) in edges:
        start = positions[n1]
        end = positions[n2]
        ax.plot([start[0], end[0]], [start[1], end[1]], c, linestyle='--', linewidth=1.5)

# Draw forklift markers
markers = {}
for forklift in current_routes.keys():
    start_pos = positions[current_routes[forklift][0]]
    marker, = ax.plot([start_pos[0]], [start_pos[1]], 'o',
                      color=colors[forklift], markersize=8, label=forklift)
    markers[forklift] = marker

ax.legend()


# Tracking Forklift Progress

# For each forklift, track:
# Current segment index
# Distance covered in the segment
# Current speed
# Whether it is waiting (loading/unloading)
# Accumulated waiting time
progress = {}
for forklift in current_routes:
    progress[forklift] = {
        'seg': 0,
        'distance_covered': 0.0,
        'current_speed': 0.0,
        'waiting': False,
        'wait_time': 0.0
    }


# Animation Update Function

def update(frame):
    for forklift in list(current_routes.keys()):
        segments = forklift_segments[forklift]
        prog = progress[forklift]

        # Check if the route is finished
        if prog['seg'] >= len(segments):
            # Select a new random route from the pool
            new_route = random.choice(routes_pool[forklift])
            current_routes[forklift] = new_route
            forklift_segments[forklift] = compute_segments(new_route)
            progress[forklift] = {
                'seg': 0,
                'distance_covered': 0.0,
                'current_speed': 0.0,
                'waiting': False,
                'wait_time': 0.0
            }
            # Place the marker at the new starting point
            start_pos = positions[new_route[0]]
            markers[forklift].set_data([start_pos[0]], [start_pos[1]])
            continue

        # Check for waiting (loading/unloading) mode
        if prog['waiting']:
            prog['wait_time'] += dt
            if prog['wait_time'] >= load_unload_time:
                prog['waiting'] = False
                prog['wait_time'] = 0.0
                prog['current_speed'] = 0.0  # Restart from zero speed after waiting
            else:
                # Keep the marker at the current position while waiting
                segment = segments[prog['seg']]
                ratio = prog['distance_covered'] / segment['distance_m']
                pos_current = segment['start'] + ratio * (segment['end'] - segment['start'])
                markers[forklift].set_data([pos_current[0]], [pos_current[1]])
                continue

        # Update movement- acceleration and progress along the segment
        segment = segments[prog['seg']]
        seg_distance = segment['distance_m']

        # Accelerate until reaching maximum speed
        if prog['current_speed'] < max_speed:
            prog['current_speed'] += acceleration * dt
            if prog['current_speed'] > max_speed:
                prog['current_speed'] = max_speed

        move_dist = prog['current_speed'] * dt
        prog['distance_covered'] += move_dist

        if prog['distance_covered'] >= seg_distance:
            # End of the segment reached
            prog['distance_covered'] = seg_distance
            pos_current = segment['start'] + (segment['end'] - segment['start'])
            markers[forklift].set_data([pos_current[0]], [pos_current[1]])
            # Enter waiting mode for 120 seconds
            prog['waiting'] = True
            prog['wait_time'] = 0.0
            # Move to the next segment
            prog['seg'] += 1
            prog['distance_covered'] = 0.0
        else:
            # Continue moving along the segment
            ratio = prog['distance_covered'] / seg_distance
            pos_current = segment['start'] + ratio * (segment['end'] - segment['start'])
            markers[forklift].set_data([pos_current[0]], [pos_current[1]])

    return list(markers.values())


# simulation

ani = animation.FuncAnimation(
    fig, update,
    frames=num_frames,
    interval=dt*1000,
    blit=True
)

plt.show()
