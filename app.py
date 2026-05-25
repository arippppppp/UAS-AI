from flask import Flask, request, jsonify
from flask_cors import CORS
import osmnx as ox
import networkx as nx

app = Flask(__name__)
CORS(app)

print("Sedang memuat sistem Peta UNIB (Kendaraan & Pejalan Kaki)...")

place_name = "Universitas Bengkulu, Bengkulu, Indonesia"

# Load graph
G_drive = ox.graph_from_place(place_name, network_type='all')
G_walk = ox.graph_from_place(place_name, network_type='walk')

print("Sistem Peta Web Siap!")

@app.route('/')
def home():
    return jsonify({
        "status": "Backend Flask aktif"
    })

@app.route('/cari_rute', methods=['POST'])
def cari_rute():
    try:
        data = request.json

        start_latlng = data['start']
        end_latlng = data['end']
        mode = data['mode']

        # Pilih graph berdasarkan mode
        G = G_walk if mode == 'walk' else G_drive

        # Cari node terdekat
        start_node = ox.distance.nearest_nodes(
            G,
            start_latlng[1],
            start_latlng[0]
        )

        end_node = ox.distance.nearest_nodes(
            G,
            end_latlng[1],
            end_latlng[0]
        )

        # Algoritma A*
        route = nx.astar_path(
            G,
            start_node,
            end_node,
            weight='length'
        )

        # Hitung jarak
        distance = int(
            nx.shortest_path_length(
                G,
                start_node,
                end_node,
                weight='length'
            )
        )

        # Format koordinat
        route_coords = [
            [G.nodes[n]['y'], G.nodes[n]['x']]
            for n in route
        ]

        return jsonify({
            'status': 'success',
            'path': route_coords,
            'distance': distance
        })

    except nx.NetworkXNoPath:
        return jsonify({
            'status': 'error',
            'message': 'Tidak ada jalan yang menghubungkan kedua titik.'
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)