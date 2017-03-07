<%
    # This is a Python code block. At rendering time the Python code below
    # will be executed and empty string will be pasted instead of <% %>.

    # Set default view for this template. From now on calls to view()
    # are merely shortcuts to view.dns()
    view.setDefaultView(view.dns)
%>
## This template just demonstrates how to use dns version rendering.
## Notece that while template-level comments are done with '##',
## the config-level comments are done using ';' since this is the
## way to do it in DNS zone files.

$TTL	01h07m01s
$ORIGIN cisco.com.

## Version is plugged into DNS file using get_dns_version()
; Domain information
galaxies IN	SOA	galaxies.com. (
	${ get_dns_version() }
	17m01s		; Refresh secondaries
	03m01s		; Retry refresh
	90d		    ; Expire
	01h07m01s	; minimum TTL / Negative caching
	)

; Name servers for this domain
;
    48h		IN	NS	ns.galaxies.com.		; Primary
    48h		IN	NS	ns1.galaxies.com.		; Secondary
    48h		IN	NS	ns2.galaxies.com.		; Secondary

## Select all the hosts and render into zone file
; Galaxies addresses
${ view(db.all()) }

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
