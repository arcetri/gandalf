<%
    # This is a Python code block. At rendering time the Python code below
    # will be executed and empty string will be pasted instead of <% %>.

    # Set default view for this template. From now on calls to view()
    # are merely shortcuts to view.hosts()
    view.setDefaultView(view.hosts)
%>#
# Example /etc/hosts entries are defined below
#
## This line is a template-level comment. It will not be rendered
## into the config file.
##
## String below is merely a Python expression that is getting evaluated.
## Whatever it evaluated into is converted to string and pasted into the template.
##
${ view(db.all()) }
##
## Nothing too sophisticated. We generate /etc/hosts entries for all
## the network entities in the CSV fileself.
## Try rendering this template by calling
##
##          ./gandalf.py examples/nodes.csv examples/templates/hosts.mako examples/rendered/hosts
##
## Or just render all the example templates by running
##
##          ./gandalf.py examples/nodes.csv examples/templates examples/rendered
##
## For slightly more sophisticated example, see dhcp.conf.mako
