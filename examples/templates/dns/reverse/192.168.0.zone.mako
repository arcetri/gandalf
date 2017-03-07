<%
    # This is a Python code block. At rendering time the Python code below
    # will be executed and empty string will be pasted instead of <% %>.

    # Set default view for this template. From now on calls to view()
    # are merely shortcuts to view.rdns()
    view.setDefaultView(view.rdns)
%>
$TTL    01d10h8m07s
$ORIGIN 0.8.10.in-addr.arpa.

@       IN      SOA     galaxies.com. (
        ${ get_dns_version() }
        06h8m07s        ; Refresh secondaries
        07m07s          ; Retry refresh
        90d             ; Expire
        01d10h8m07s     ; minimum TTL / Negative caching
        )

        48h             IN      NS      ns.galaxies.com.           ; Primary
        48h             IN      NS      ns1.galaxies.com.          ; Secondary
        48h             IN      NS      ns2.galaxies.com.          ; Secondary

## Render reverse DNS entries for the 192.168.0.0/24 network
${ view(db.search(host.ip.test(lambda s: s.startswith("192.168.0.")))) }
##
## You can render templates using command
##
##          ./gandalf.py examples/nodes.csv examples/templates examples/rendered
##
## Note that in sunsequent renderings DNS version number will be generated
## from scratch, not updated. To make Gandalf get use of the previous DNS
## version number, use command
##
##          ./gandalf.py examples/nodes.csv examples/templates examples/rendered -d examples/rendered
##
## In last case version number will be correctly updated when something changes
## in the file and left unchanged otherwise.
