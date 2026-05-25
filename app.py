from flask import Flask, request, jsonify
from flask_cors import CORS
import osmnx as ox
import networkx as nx

app = Flask(__name__)
# Mengizinkan koneksi cross-origin dari frontend Github Pages / Local HTML
CORS(app)

print("Sedang mengunduh Jaringan Jalan Universitas Bengkulu dari OpenStreetMap...")

place_name = "Universitas Bengkulu, Bengkulu, Indonesia"

# Ambil seluruh jalan internal komplit di dalam kawasan UNIB
G_drive = ox.graph_from_place(place_name, network_type='all_private')
G_walk = ox.graph_from_place(place_name, network_type='walk')

# Lakukan proyeksi koordinat (UTM) di awal agar kalkulasi A* dan Nearest Node akurat mengikuti geometri bumi
G_drive_proj = ox.project_graph(G_drive)
G_walk_proj = ox.project_graph(G_walk)

print("Sistem AI Graph Peta UNIB Siap Digunakan!")

@app.route('/')
def home():
    return jsonify({
        "status": "success",
        "message": "Backend Flask Navigasi UNIB Aktif"
    })

@app.route('/cari_rute', methods=['POST'])
def cari_rute():
    try:
        data = request.json
        start_latlng = data['start']
        end_latlng = data['end']
        mode = data['mode']

        # Tentukan graph terproyeksi yang dipakai berdasarkan pilihan tombol user
        if mode == 'walk':
            G_orig = G_walk
            G_proj = G_walk_proj
        else:
            G_orig = G_drive
            G_proj = G_drive_proj

        # Cari ID node jalan terdekat dengan akurasi koordinat bumi terproyeksi
        start_node = ox.distance.nearest_nodes(
            G_proj, 
            X=start_latlng[1], 
            Y=start_latlng[0], 
            is_projected=False
        )
        
        end_node = ox.distance.nearest_nodes(
            G_proj, 
            X=end_latlng[1], 
            Y=end_latlng[0], 
            is_projected=False
        )

        # Proses Pencarian Lintasan Terpendek Menggunakan Algoritma A* (A-Star)
        route = nx.astar_path(
            G_orig,
            start_node,
            end_node,
            weight='length'
        )

        # Hitung akumulasi total jarak rute dalam satuan Meter
        distance = int(
            nx.shortest_path_length(
                G_orig,
                start_node,
                end_node,
                weight='length'
            )
        )

        # Ekstrak kembali susunan titik koordinat lintasan jalan (Y=Lat, X=Lng) untuk dikirim ke Leaflet
        route_coords = [
            [G_orig.nodes[n]['y'], G_orig.nodes[n]['x']]
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
            'message': 'Jalur aspal terputus, tidak ada jalan penghubung riil di peta.'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f"Terjadi kesalahan sistem: {str(e)}"
        })

if __name__ == '__main__':
    # Dijalankan di port 5000 lokal komputer
    app.run(host='127.0.0.1', port=5000, debug=True)
