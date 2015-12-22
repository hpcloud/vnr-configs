#!/usr/bin/python -tt
# vim: set ts=4 sw=4 tw=79 et :


debug = True


# Log parser
def parse_log():
    records = []
    zf = open('/var/log/iptables.log', 'r')
    for line in zf:
    	fields = line.split()
        records.append([fields[0], fields[1], fields[2],
                        fields[9].split('=')[1], fields[10].split('=')[1],
                        fields[18].split('=')[1]])
    zf.close()
    return records;


# Sort source IPs by volume of hits
def ip_counts(records):
    global debug
    ip_counts = []
    for record in records:
        found = False
        for ip in ip_counts:
            if record[3] == ip[0]:
                ip[1] = ip[1] + 1
                found = True
                break;
        if not found:
            ip_counts.append([record[3], 1])
    ip_counts = sorted(ip_counts, key=lambda x: -x[1]);
    if debug:
        for ip in ip_counts:
            print ip
    return ip_counts;


# Sort source IPs by port
def port_counts(records):
    global debug
    port_counts = []
    for record in records:
        found = False
        for port in port_counts:
            if record[3] == port[0]:
                if record[5] == port[1]:
                    port[2] = port[2] + 1
                    found = True
                    break;
        if not found:
            port_counts.append([record[3], record[5], 1])
    port_counts = sorted(port_counts, key=lambda x: (x[0], x[1]))
    if debug:
        for port in port_counts:
            print port
    return port_counts;


# Main program 
def main():
    records = parse_log()
    ipcs = ip_counts(records)
    pcs = port_counts(records)


if __name__ == '__main__':
    main()
