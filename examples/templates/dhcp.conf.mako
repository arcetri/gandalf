<%
    # This is a Python code block. At rendering time the Python code below
    # will be executed and empty string will be pasted instead of <% %>.

    # Set default view for this template. From now on calls to view()
    # are merely shortcuts to view.dhcp()
    view.setDefaultView(view.dhcp)
%>#
# Example DHCP entries are defined below.
#
## Note that in this file comments are made using ';' symbol because
## this is DHCP file syntax. However, template-level comments are still
## to be done in '##' style.
##
## Below we will do some more querying compared to /etc/hosts file.
## Every query will merely select one entry from CSV file but in somewhat
## sophisticated way.
##
## Select all entries from VLAN 1010. It happens to be
## the case that only 'andromeda' host matches it.
##
# Hosts from VLAN 1010:
#
${ view(db.search(host.vlan == 1010)) }
##
## Select all entries that are from VLAN 2020 and are compute nodes.
## This query brings in 'whirlpool' host. Note that we provide an additional
## option to view rendering function to include PXE boot filename.
#
# Compute nodes from VLAN 1010:
#
${ view(db.search((host.vlan == 2020) & (host.type == "comp")), filename="shim.efi") }
##
## The following query selects all the hosts that have an IP address
## starting with "192.168.0.". Note how we use custom lambda function for that.
#
# Nodes from 192.168.0.0/24 network:
#
${ view(db.search(host.ip.test(lambda s: s.startswith("192.168.0.")))) }
## Try rendering this template by calling
##
##          ./gandalf.py examples/nodes.csv examples/templates/dhcp.conf.mako examples/rendered/dhcp.conf.mako
##
## Or just render all the example templates by running
##
##          ./gandalf.py examples/nodes.csv examples/templates examples/rendered
##
