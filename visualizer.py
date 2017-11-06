import sys,random
import networkx as nx
import matplotlib.pyplot as plt
from pprint import pprint

from common import *



def main():
	"""Execute the main actions of the network visualizer program

	Arguments:
		static - draw the static network

		agency,agency_2,... - the transit agency for which we want to retrieve routes

	"""

	# With the "static" argument, create images of the static network
	if len(sys.argv) > 2 and (sys.argv[1] == "static" or sys.argv[1] == "-s" ):

		metrics = []

		for agency in sys.argv[2].split(" "):

			G, stops_list, connections_list = create_static_network(agency)
			draw_static_network(G,stops_list)

			# agency_metrics = calculate_all_agency_metrics(G, connections_list, stops_list, agency)
			# metrics.append(agency + "," + ",".join(str(value) for value in agency_metrics.values()))

			# print("Calculated metrics for: " + agency + "\t\t")

		metrics = ["city," + ",".join(str(value) for value in agency_metrics.keys())] + metrics
		print("\n" + "\n".join(metrics) + "\n")

	# With wrong arguments, print usage help message
	else:
		print("Usage: visualizer <static|...> <agency>[,<agency_2>,...]")

		

# ===============================================
# =			Static Network Visualization 		=
# ===============================================

def create_static_network(directory):
	"""Draw an image for the pre-built static network of the transport system."""

	# Read the network files
	stops_list = read_stops_file(directory)
	connections_list = read_connections_file(directory)

	# Build the graph object, add stops and connections
	G = nx.Graph()
	G.add_nodes_from(convert_stops_to_tuples(stops_list))
	G.add_edges_from(convert_connections_to_tuples(connections_list))

	# G = nx.connected_components(G)

	return G, stops_list, connections_list



# ===============================================
# =				Metrics Calculation				=
# ===============================================

def calculate_all_agency_metrics(G, connections_list, stops_list, agency):

	# Area and earth radius presets
	if agency == 'ttc':
		radius = 6368.262
		area = 630
	elif agency == 'lametro':
		radius = 6371.57
		area = 1214
	elif agency == 'sf-muni':
		radius = 6370.158
		area = 121
	else: # Radius of the Earth in kilometeres, used for 37 degrees north, also 6371.001 on average
		radius = 6373
		area = 1

	metrics = {}


	# metrics['total_length'] = sum(connection['length'] for connection in connections_list)
	# metrics['total_length_normalized'] = metrics['total_length']/area

	# metrics['average_connection_length'] = metrics['total_length']/len(connections_list)

	# metrics['average_shortest_path'] = nx.average_shortest_path_length(G,weight='length')
	# metrics['average_straight_distance'] = calculate_average_straight_distance(G, stops_list, radius)
	# metrics['average_detour_normalized'] = ((metrics['average_shortest_path']-metrics['average_straight_distance'])
	# 	/metrics['average_straight_distance'])

	stops_sum = 0
	distance_sum = 0

	for i in range(1,10):

		random.seed()
		new_stops, new_distance = calculate_coverage(G, stops_list, radius, 1000)
		stops_sum = stops_sum + new_stops
		distance_sum = distance_sum + new_distance

	metrics['coverage_stops'], metrics['coverage_distance'] = stops_sum/10, distance_sum/10

	# metrics['average_clustering'] = nx.average_clustering(G,weight='length')
	# metrics['degree_connectivity'] = nx.average_degree_connectivity(G,weight='length')

	return metrics


def calculate_average_straight_distance(G, stops_list, radius):

	sum = 0

	for i in range(0,len(stops_list)):
		for j in range(i+1,len(stops_list)):

			stop_1 = stops_list[i]
			stop_2 = stops_list[j]

			if stop_1 != stop_2:
				distance = calculate_straight_distance(stop_1['lat'], stop_1['lon'], stop_2['lat'], stop_2['lon'], radius)
				sum = sum + distance
		
		print("Calculated distances for " + str( i + 1 ) + "/" + str(len(G.nodes)) + " stops", end="\r")
	
	return 2*sum/(len(G.nodes)*(len(G.nodes)-1))


def calculate_coverage(G, stops_list, radius, sample_size):

	lat_dict = {float(stop['lat']):stop for stop in stops_list}
	lon_dict = {float(stop['lon']):stop for stop in stops_list}

	bounding_box = { 'left': min(lon_dict), 'right': max(lon_dict), 'top': max(lat_dict), 'bottom': min(lat_dict)}

	cutoff_high_deg = 0.0072	# 800m
	cutoff_low_deg = 0.0036  	# 400m
	walk_km = 0.4		# 400m

	sample = []
	close_stops_sum = 0
	least_distance_sum = 0
	x = 0
	i = 0

	while x < sample_size and i < 10000:

		i = i + 1

		random_lat = random.uniform(bounding_box['top'], bounding_box['bottom'])
		random_lon = random.uniform(bounding_box['left'], bounding_box['right'])

		cutoff_square_stops = [ stop for stop in stops_list if (
			(random_lat < float(stop['lat'])+cutoff_high_deg and random_lat > float(stop['lat'])-cutoff_high_deg)
			and (random_lon < float(stop['lon'])+cutoff_high_deg and random_lon > float(stop['lon'])-cutoff_high_deg))]

		if(len(cutoff_square_stops) > 0):

			close_square_stops = [ stop for stop in cutoff_square_stops if (
				(random_lat < float(stop['lat'])+cutoff_low_deg and random_lat > float(stop['lat'])-cutoff_low_deg)
				and (random_lon < float(stop['lon'])+cutoff_low_deg and random_lon > float(stop['lon'])-cutoff_low_deg))]
			
			close_stops_distances = list(map(
				lambda x: calculate_straight_distance(random_lat, random_lon, x['lat'], x['lon'], radius),
				close_square_stops))

			close_stops_count = len(list(filter(lambda x: x < walk_km, close_stops_distances)))
			close_stops_sum = close_stops_sum + close_stops_count

			if close_stops_count > 0:

				least_distance = min(close_stops_distances)

			else:
				cutoff_stops_distances = map(
					lambda x: calculate_straight_distance(random_lat, random_lon, x['lat'], x['lon'], radius),
					cutoff_square_stops)
				least_distance = min(list(cutoff_stops_distances))

			least_distance_sum = least_distance_sum + least_distance

			x = x + 1
			print("Calculated coverage for " + str(x) + "/" + str(sample_size) + " points", end="\r")

	return close_stops_sum/sample_size, least_distance_sum/sample_size


# ===============================================
# =				Graph Visualization				=
# ===============================================

def draw_static_network(G,stops_list):

	nx.draw_networkx(
		G,
		node_size=0.1,
		with_labels=False
		,edge_color="#AAAAAA"
		,node_color="black"
		,arrows=False
		,pos=convert_stops_to_positions(stops_list))
	# plt.show()



	# print("Bridges:")
	bridges, G2 = get_graph_bridges(G)
	# # print(bridges)
	nx.draw_networkx(G2,node_size=0.1,edge_color="red",with_labels=False,arrows=False,pos=convert_stops_to_positions(stops_list))
	

	# print("Center:")
	# center, G3 = get_graph_center(G)
	# print(center)
	# nx.draw_networkx(G3,node_size=15,node_color="green",with_labels=False,arrows=False,pos=convert_stops_to_positions(stops_list))


	plt.show()
	# plt.savefig("bridges_800", dpi=800)


def get_graph_bridges(G):

	bridges = list(nx.bridges(G))
	non_bridges = [edge for edge in G.edges if edge not in bridges]

	G2 = G.copy()
	G2.remove_edges_from(non_bridges)
	G2.remove_nodes_from(list(nx.isolates(G2)))

	return bridges, G2


def get_graph_center(G):

	center= nx.center(G)
	non_center = [node for node in G.nodes if node not in center]

	G2 = G.copy()
	G2.remove_nodes_from(non_center)

	return center, G2


# ===============================================
if __name__ == "__main__":
    main()
