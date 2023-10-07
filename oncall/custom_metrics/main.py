import time
import psutil
import prometheus_client

def collect_network_traffic_metrics():
    registry=prometheus_client.CollectorRegistry(auto_describe=True)
    g1 = prometheus_client.Gauge('network_tx_bytes', 'Shows input traffic', registry=registry)
    g2 = prometheus_client.Gauge('network_rx_bytes', 'Shows output traffic', registry=registry)
    g1.set_to_current_time()
    g2.set_to_current_time()

    network_stats = psutil.net_io_counters(pernic=True)

    total_tx_bytes = 0
    total_rx_bytes = 0
    for _, stats in network_stats.items():
        total_tx_bytes += stats.bytes_sent
        total_rx_bytes += stats.bytes_recv

    g1.set(total_tx_bytes)
    g2.set(total_rx_bytes)
    prometheus_client.write_to_textfile('/var/lib/node-exporter/textfile_collector/my_metrics.prom', registry)

if __name__ == '__main__':
    while True:
        collect_network_traffic_metrics()
        time.sleep(1)
